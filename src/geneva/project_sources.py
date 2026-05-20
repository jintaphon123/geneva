from __future__ import annotations

import hashlib
import html
import json
import os
import re
import sqlite3
import uuid
import zipfile
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from src.memdir.brain_engine import DB_PATH, init_db
from src.memdir.paths import get_data_dir
from src.services.compact import ContextSourceBlock
from src.token_estimation import count_tokens

SourceFetcher = Callable[[str], str]

INCLUDE_POLICIES = {"include", "exclude"}
PARSE_STATUSES = {"pending", "ready", "failed", "unsupported", "stale"}
SOURCE_TYPES = {"text", "markdown", "url", "pdf", "docx"}
TEXT_SOURCE_TYPES = {"text", "markdown"}
DOCUMENT_SOURCE_TYPES = {"pdf", "docx"}

CONTEXT_SOURCE_LIMIT = 8
CONTEXT_MAX_CHARS_PER_SOURCE = 6_000


def _db_path() -> Path:
    override = os.environ.get("GENEVA_BRAIN_DB_PATH")
    return Path(override).expanduser() if override else DB_PATH


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_segment(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return (clean or "source")[:96]


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_metadata(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _html_to_text(raw: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</(p|div|li|h[1-6]|tr)>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", text)).strip()


def _default_url_fetcher(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Geneva/1.0"})
    with urlopen(request, timeout=15) as response:
        body = response.read(2_000_000)
        content_type = response.headers.get("content-type", "")
        encoding = response.headers.get_content_charset() or "utf-8"
    text = body.decode(encoding, errors="replace")
    if "html" in content_type.lower() or "<html" in text[:1000].lower():
        return _html_to_text(text)
    return text.strip()


def _validate_url(url: str) -> str:
    clean_url = url.strip()
    parsed = urlparse(clean_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL source must use http or https")
    return clean_url


def _decode_pdf_literal(raw: bytes) -> str:
    output: list[str] = []
    index = 0
    escapes = {
        ord("n"): "\n",
        ord("r"): "\r",
        ord("t"): "\t",
        ord("b"): "\b",
        ord("f"): "\f",
        ord("("): "(",
        ord(")"): ")",
        ord("\\"): "\\",
    }
    while index < len(raw):
        byte = raw[index]
        if byte != ord("\\"):
            output.append(chr(byte))
            index += 1
            continue
        index += 1
        if index >= len(raw):
            break
        escaped = raw[index]
        if escaped in escapes:
            output.append(escapes[escaped])
            index += 1
            continue
        if ord("0") <= escaped <= ord("7"):
            octal = bytes([escaped])
            index += 1
            for _ in range(2):
                if index < len(raw) and ord("0") <= raw[index] <= ord("7"):
                    octal += bytes([raw[index]])
                    index += 1
            output.append(chr(int(octal, 8)))
            continue
        if escaped in {ord("\n"), ord("\r")}:
            index += 1
            if escaped == ord("\r") and index < len(raw) and raw[index] == ord("\n"):
                index += 1
            continue
        output.append(chr(escaped))
        index += 1
    return "".join(output)


def _pdf_streams(data: bytes) -> list[bytes]:
    streams: list[bytes] = []
    for match in re.finditer(rb"(.*?)stream\r?\n(.*?)\r?\nendstream", data, re.DOTALL):
        header = match.group(1)[-800:]
        stream = match.group(2).strip(b"\r\n")
        if b"FlateDecode" in header:
            try:
                stream = zlib.decompress(stream)
            except zlib.error:
                pass
        streams.append(stream)
    return streams


def _extract_pdf_text_fallback(path: Path) -> str:
    data = path.read_bytes()
    if not data.startswith(b"%PDF-"):
        raise ValueError("not a PDF file")
    chunks = [data, *_pdf_streams(data)]
    parts: list[str] = []
    literal = rb"\((?:\\.|[^\\()])*\)"
    for chunk in chunks:
        for match in re.finditer(literal + rb"\s*Tj", chunk, re.DOTALL):
            raw = match.group(0).rsplit(b")", 1)[0][1:]
            text = _decode_pdf_literal(raw).strip()
            if text:
                parts.append(text)
        for array in re.finditer(rb"\[(.*?)\]\s*TJ", chunk, re.DOTALL):
            text_parts = []
            for literal_match in re.finditer(literal, array.group(1), re.DOTALL):
                text_parts.append(_decode_pdf_literal(literal_match.group(0)[1:-1]))
            text = "".join(text_parts).strip()
            if text:
                parts.append(text)
    deduped: list[str] = []
    seen: set[str] = set()
    for part in parts:
        if part not in seen:
            deduped.append(part)
            seen.add(part)
    return "\n".join(deduped).strip()


def _extract_pdf_text(path: Path) -> tuple[str, str]:
    parser_errors: list[str] = []
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
        if text:
            return text, "pypdf"
    except Exception as exc:
        parser_errors.append(f"pypdf: {exc}")

    try:
        from PyPDF2 import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
        if text:
            return text, "PyPDF2"
    except Exception as exc:
        parser_errors.append(f"PyPDF2: {exc}")

    try:
        from pdfminer.high_level import extract_text  # type: ignore

        text = str(extract_text(str(path)) or "").strip()
        if text:
            return text, "pdfminer"
    except Exception as exc:
        parser_errors.append(f"pdfminer: {exc}")

    try:
        text = _extract_pdf_text_fallback(path)
        if text:
            return text, "pdf-stdlib"
    except Exception as exc:
        parser_errors.append(f"pdf-stdlib: {exc}")

    detail = "; ".join(error[:160] for error in parser_errors if error)
    raise ValueError(detail or "no readable text extracted from PDF")


def _extract_docx_text(path: Path) -> str:
    paragraphs: list[str] = []
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    xml_names = ["word/document.xml"]
    with zipfile.ZipFile(path) as archive:
        xml_names.extend(
            name
            for name in archive.namelist()
            if re.match(r"word/(header|footer)\d+\.xml$", name)
        )
        for name in xml_names:
            try:
                raw = archive.read(name)
            except KeyError:
                continue
            root = ET.fromstring(raw)
            for paragraph in root.iter(f"{namespace}p"):
                pieces: list[str] = []
                for node in paragraph.iter():
                    if node.tag == f"{namespace}t" and node.text:
                        pieces.append(node.text)
                    elif node.tag == f"{namespace}tab":
                        pieces.append("\t")
                    elif node.tag == f"{namespace}br":
                        pieces.append("\n")
                text = "".join(pieces).strip()
                if text:
                    paragraphs.append(text)
    text = "\n\n".join(paragraphs).strip()
    if not text:
        raise ValueError("no readable text extracted from DOCX")
    return text


class ProjectSourceStore:
    def __init__(self) -> None:
        init_db()
        self._ensure_tables()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(_db_path())
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS project_sources (
                    id              TEXT PRIMARY KEY,
                    project_id      TEXT NOT NULL,
                    source_type     TEXT NOT NULL,
                    title           TEXT NOT NULL,
                    uri             TEXT DEFAULT '',
                    content_hash    TEXT NOT NULL,
                    snapshot_path   TEXT NOT NULL,
                    parse_status    TEXT NOT NULL DEFAULT 'ready',
                    include_policy  TEXT NOT NULL DEFAULT 'include',
                    token_estimate  INTEGER DEFAULT 0,
                    metadata        TEXT DEFAULT '{}',
                    parse_error     TEXT DEFAULT NULL,
                    created_at      TEXT NOT NULL,
                    updated_at      TEXT NOT NULL,
                    last_indexed_at TEXT DEFAULT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_project_sources_project_ready
                    ON project_sources(project_id, include_policy, parse_status);
                CREATE INDEX IF NOT EXISTS idx_project_sources_project_updated
                    ON project_sources(project_id, updated_at DESC);
                """
            )

    def _snapshot_dir(self, project_id: str) -> Path:
        return get_data_dir() / "sources" / _safe_segment(project_id)

    def _write_snapshot(self, project_id: str, source_id: str, source_type: str, content: str) -> Path:
        snapshot_dir = self._snapshot_dir(project_id)
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        suffix = ".md" if source_type == "markdown" else ".txt"
        snapshot_path = snapshot_dir / f"{_safe_segment(source_id)}{suffix}"
        snapshot_path.write_text(content, encoding="utf-8")
        return snapshot_path

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": str(row["id"]),
            "project_id": str(row["project_id"]),
            "source_type": str(row["source_type"]),
            "title": str(row["title"] or ""),
            "uri": str(row["uri"] or ""),
            "content_hash": str(row["content_hash"] or ""),
            "snapshot_path": str(row["snapshot_path"] or ""),
            "parse_status": str(row["parse_status"] or "ready"),
            "include_policy": str(row["include_policy"] or "include"),
            "token_estimate": int(row["token_estimate"] or 0),
            "metadata": _parse_metadata(row["metadata"]),
            "parse_error": row["parse_error"],
            "created_at": str(row["created_at"] or ""),
            "updated_at": str(row["updated_at"] or ""),
            "last_indexed_at": row["last_indexed_at"],
        }

    def _insert_source_record(
        self,
        *,
        project_id: str,
        title: str,
        content: str,
        source_type: str,
        uri: str = "",
        parse_status: str = "ready",
        include_policy: str = "include",
        metadata: dict[str, Any] | None = None,
        parse_error: str | None = None,
    ) -> dict[str, Any]:
        clean_project_id = project_id.strip()
        clean_title = title.strip() or "Untitled source"
        clean_source_type = source_type.strip().lower()
        clean_status = parse_status.strip().lower()
        clean_policy = include_policy.strip().lower()
        clean_content = content.strip()
        if not clean_project_id:
            raise ValueError("Project id is required")
        if clean_source_type not in SOURCE_TYPES:
            raise ValueError("source_type must be text, markdown, url, pdf, or docx")
        if clean_status not in PARSE_STATUSES:
            raise ValueError("parse_status must be pending, ready, failed, unsupported, or stale")
        if clean_policy not in INCLUDE_POLICIES:
            raise ValueError("include_policy must be include or exclude")

        source_id = str(uuid.uuid4())
        now = _now()
        snapshot_path = self._write_snapshot(clean_project_id, source_id, clean_source_type, clean_content)
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO project_sources (
                    id, project_id, source_type, title, uri, content_hash, snapshot_path,
                    parse_status, include_policy, token_estimate, metadata, parse_error,
                    created_at, updated_at, last_indexed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    clean_project_id,
                    clean_source_type,
                    clean_title,
                    uri,
                    _hash_text(clean_content),
                    str(snapshot_path),
                    clean_status,
                    clean_policy,
                    count_tokens(clean_content) if clean_content else 0,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    parse_error,
                    now,
                    now,
                    now if clean_status == "ready" else None,
                ),
            )
        source = self.get_source(clean_project_id, source_id)
        return source or {}

    def add_text_source(
        self,
        *,
        project_id: str,
        title: str,
        content: str,
        source_type: str = "text",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        clean_project_id = project_id.strip()
        clean_title = title.strip() or "Untitled source"
        clean_content = content.strip()
        clean_source_type = source_type.strip().lower()
        if not clean_project_id:
            raise ValueError("Project id is required")
        if clean_source_type not in TEXT_SOURCE_TYPES:
            raise ValueError("Text source type must be text or markdown")
        if not clean_content:
            raise ValueError("Source content is required")

        return self._insert_source_record(
            project_id=clean_project_id,
            title=clean_title,
            content=clean_content,
            source_type=clean_source_type,
            metadata=metadata,
        )

    def add_document_source(
        self,
        *,
        project_id: str,
        path: str | Path,
        title: str = "",
    ) -> dict[str, Any]:
        clean_project_id = project_id.strip()
        if not clean_project_id:
            raise ValueError("Project id is required")
        document_path = Path(path).expanduser()
        source_type = document_path.suffix.lower().lstrip(".")
        if source_type not in DOCUMENT_SOURCE_TYPES:
            raise ValueError("Document source type must be pdf or docx")

        metadata: dict[str, Any] = {
            "file_name": document_path.name,
            "source_path": str(document_path),
            "suffix": document_path.suffix.lower(),
        }
        parse_status = "ready"
        parse_error: str | None = None
        text = ""
        parser = ""

        if not document_path.exists():
            parse_status = "failed"
            parse_error = f"document not found: {document_path}"
        else:
            try:
                if source_type == "pdf":
                    text, parser = _extract_pdf_text(document_path)
                else:
                    text = _extract_docx_text(document_path)
                    parser = "docx-zipxml"
            except Exception as exc:
                parse_status = "failed"
                parse_error = str(exc)

        if parse_status == "ready" and not text.strip():
            parse_status = "failed"
            parse_error = "document parser returned no readable text"
        metadata.update(
            {
                "parser": parser or ("pdf" if source_type == "pdf" else "docx-zipxml"),
                "extracted_chars": len(text.strip()),
            }
        )

        return self._insert_source_record(
            project_id=clean_project_id,
            title=title.strip() or document_path.name,
            content=text,
            source_type=source_type,
            uri=str(document_path),
            parse_status=parse_status,
            metadata=metadata,
            parse_error=parse_error,
        )

    def add_url_source(
        self,
        *,
        project_id: str,
        url: str,
        title: str = "",
        fetcher: SourceFetcher | None = None,
    ) -> dict[str, Any]:
        clean_project_id = project_id.strip()
        clean_url = _validate_url(url)
        if not clean_project_id:
            raise ValueError("Project id is required")
        page_text = (fetcher or _default_url_fetcher)(clean_url).strip()
        if not page_text:
            raise ValueError("URL source returned no readable text")
        metadata = {"fetched_at": _now()}
        source = self.add_text_source(
            project_id=clean_project_id,
            title=title.strip() or clean_url,
            content=page_text,
            source_type="text",
            metadata=metadata,
        )
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE project_sources
                SET source_type='url', uri=?, metadata=?, updated_at=?
                WHERE id=? AND project_id=?
                """,
                (
                    clean_url,
                    json.dumps(metadata, ensure_ascii=False),
                    _now(),
                    source["id"],
                    clean_project_id,
                ),
            )
        return self.get_source(clean_project_id, source["id"]) or source

    def get_source(self, project_id: str, source_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM project_sources WHERE project_id=? AND id=?",
                (project_id, source_id),
            ).fetchone()
        return self._row_to_dict(row) if row is not None else None

    def get_source_by_id(self, source_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM project_sources WHERE id=?", (source_id,)).fetchone()
        return self._row_to_dict(row) if row is not None else None

    def list_sources(self, project_id: str) -> dict[str, Any]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM project_sources
                WHERE project_id=?
                ORDER BY updated_at DESC, created_at DESC
                """,
                (project_id,),
            ).fetchall()
        sources = [self._row_to_dict(row) for row in rows]
        return {"sources": sources, "count": len(sources)}

    def update_source(
        self,
        project_id: str,
        source_id: str,
        *,
        title: str | None = None,
        include_policy: str | None = None,
        parse_status: str | None = None,
        parse_error: str | None = None,
    ) -> dict[str, Any] | None:
        updates: dict[str, Any] = {}
        if title is not None:
            clean_title = title.strip()
            if not clean_title:
                raise ValueError("Source title is required")
            updates["title"] = clean_title
        if include_policy is not None:
            clean_policy = include_policy.strip().lower()
            if clean_policy not in INCLUDE_POLICIES:
                raise ValueError("include_policy must be include or exclude")
            updates["include_policy"] = clean_policy
        if parse_status is not None:
            clean_status = parse_status.strip().lower()
            if clean_status not in PARSE_STATUSES:
                raise ValueError("parse_status must be pending, ready, failed, unsupported, or stale")
            updates["parse_status"] = clean_status
        if parse_error is not None:
            updates["parse_error"] = parse_error.strip() or None
        if not updates:
            return self.get_source(project_id, source_id)

        updates["updated_at"] = _now()
        assignments = ", ".join(f"{key}=?" for key in updates)
        with self._conn() as conn:
            cursor = conn.execute(
                f"UPDATE project_sources SET {assignments} WHERE project_id=? AND id=?",
                (*updates.values(), project_id, source_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_source(project_id, source_id)

    def delete_source(self, project_id: str, source_id: str) -> bool:
        source = self.get_source(project_id, source_id)
        if source is None:
            return False
        with self._conn() as conn:
            cursor = conn.execute(
                "DELETE FROM project_sources WHERE project_id=? AND id=?",
                (project_id, source_id),
            )
        snapshot_path = Path(str(source.get("snapshot_path") or ""))
        try:
            if snapshot_path.exists():
                snapshot_path.unlink()
        except OSError:
            pass
        return cursor.rowcount > 0

    def read_snapshot(self, source_id: str) -> str:
        source = self.get_source_by_id(source_id)
        if source is None:
            return ""
        snapshot_path = Path(str(source.get("snapshot_path") or ""))
        try:
            return snapshot_path.read_text(encoding="utf-8")
        except OSError:
            return ""

    def included_ready_sources(self, project_id: str, limit: int = CONTEXT_SOURCE_LIMIT) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 20))
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM project_sources
                WHERE project_id=? AND include_policy='include' AND parse_status='ready'
                ORDER BY updated_at DESC, created_at DESC
                LIMIT ?
                """,
                (project_id, safe_limit),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def context_preview(
        self,
        project_id: str,
        *,
        limit: int = CONTEXT_SOURCE_LIMIT,
        max_chars_per_source: int = CONTEXT_MAX_CHARS_PER_SOURCE,
    ) -> dict[str, Any]:
        sources = self.included_ready_sources(project_id, limit=limit)
        rendered: list[str] = []
        preview_sources: list[dict[str, Any]] = []
        for source in sources:
            content = self.read_snapshot(str(source["id"])).strip()
            if not content:
                continue
            excerpt = content[:max_chars_per_source]
            rendered.append(f"### {source['title']}\n{excerpt}")
            preview_sources.append(source)
        return {
            "preview": "\n\n".join(rendered),
            "sources": preview_sources,
            "count": len(preview_sources),
        }

    def context_source_blocks(
        self,
        project_id: str,
        *,
        limit: int = CONTEXT_SOURCE_LIMIT,
        max_chars_per_source: int = CONTEXT_MAX_CHARS_PER_SOURCE,
    ) -> list[ContextSourceBlock]:
        preview = self.context_preview(
            project_id,
            limit=limit,
            max_chars_per_source=max_chars_per_source,
        )
        blocks: list[ContextSourceBlock] = []
        for source in preview["sources"]:
            content = self.read_snapshot(str(source["id"])).strip()
            if not content:
                continue
            text = f"## Project Source: {source['title']}\n{content[:max_chars_per_source]}"
            blocks.append(
                ContextSourceBlock(
                    source_type="project_source",
                    label=f"Project source: {source['title']}",
                    text=text,
                    reason="Included ready project source attached to the active project.",
                    metadata={
                        "project_id": project_id,
                        "source_id": source["id"],
                        "title": source["title"],
                        "source_type": source["source_type"],
                        "uri": source["uri"],
                    },
                )
            )
        return blocks


def project_source_context_blocks(project_id: str) -> list[ContextSourceBlock]:
    return ProjectSourceStore().context_source_blocks(project_id)
