from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SUPPORTED_PARSE_SUFFIXES = frozenset({".txt", ".md", ".markdown", ".html", ".htm", ".json", ".pdf", ".docx"})


@dataclass(frozen=True)
class DocumentParseResult:
    status: str
    path: str
    suffix: str
    blocks: list[dict[str, Any]]
    text: str
    parser: str
    error: str = ""


@dataclass(frozen=True)
class DocumentGenerateResult:
    status: str
    path: str
    bytes_written: int
    format: str


@dataclass(frozen=True)
class DocumentVerifyResult:
    status: str
    path: str
    exists: bool
    bytes: int
    line_count: int
    citation_markers: list[str]
    warnings: list[str]


class DocumentRuntime:
    """Local-first document parser, generator, and verification contract."""

    def parse(self, path: Path) -> DocumentParseResult:
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_PARSE_SUFFIXES:
            return DocumentParseResult(
                status="unsupported",
                path=str(path),
                suffix=suffix,
                blocks=[],
                text="",
                parser="none",
                error=f"unsupported document type: {suffix}",
            )
        if suffix in {".txt", ".md", ".markdown"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            return DocumentParseResult(
                status="ok",
                path=str(path),
                suffix=suffix,
                blocks=self._text_blocks(text),
                text=text,
                parser="plain-text",
            )
        if suffix in {".html", ".htm"}:
            raw = path.read_text(encoding="utf-8", errors="replace")
            text = re.sub(r"<[^>]+>", " ", raw)
            text = re.sub(r"\s+", " ", text).strip()
            return DocumentParseResult(
                status="ok",
                path=str(path),
                suffix=suffix,
                blocks=self._text_blocks(text),
                text=text,
                parser="html-text",
            )
        if suffix == ".json":
            raw = path.read_text(encoding="utf-8", errors="replace")
            parsed = json.loads(raw)
            text = json.dumps(parsed, ensure_ascii=False, indent=2)
            return DocumentParseResult(
                status="ok",
                path=str(path),
                suffix=suffix,
                blocks=[{"type": "json", "content": parsed}],
                text=text,
                parser="json",
            )
        return self._parse_with_docling(path)

    def generate_markdown(
        self,
        *,
        output_path: Path,
        title: str,
        markdown: str = "",
        sections: list[dict[str, Any]] | None = None,
        overwrite: bool = False,
    ) -> DocumentGenerateResult:
        if output_path.exists() and not overwrite:
            raise FileExistsError(f"refusing to overwrite existing document: {output_path}")
        body = markdown.strip()
        if not body:
            lines = [f"# {title.strip() or 'Untitled'}", ""]
            for section in sections or []:
                heading = str(section.get("title") or "").strip()
                content = str(section.get("content") or "").strip()
                if heading:
                    lines.extend([f"## {heading}", ""])
                if content:
                    lines.extend([content, ""])
            body = "\n".join(lines).rstrip() + "\n"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(body, encoding="utf-8")
        return DocumentGenerateResult(
            status="ok",
            path=str(output_path),
            bytes_written=output_path.stat().st_size,
            format=output_path.suffix.lower().lstrip(".") or "md",
        )

    def verify(self, path: Path) -> DocumentVerifyResult:
        warnings: list[str] = []
        if not path.exists():
            return DocumentVerifyResult(
                status="missing",
                path=str(path),
                exists=False,
                bytes=0,
                line_count=0,
                citation_markers=[],
                warnings=["document does not exist"],
            )
        data = path.read_bytes()
        text = data.decode("utf-8", errors="replace")
        citation_markers = sorted(set(re.findall(r"\[(?:S|E)?\d+\]", text)))
        if path.suffix.lower() in {".md", ".markdown"} and not citation_markers:
            warnings.append("no citation markers found")
        if len(data) == 0:
            warnings.append("document is empty")
        return DocumentVerifyResult(
            status="ok" if not warnings else "warning",
            path=str(path),
            exists=True,
            bytes=len(data),
            line_count=len(text.splitlines()),
            citation_markers=citation_markers,
            warnings=warnings,
        )

    def _parse_with_docling(self, path: Path) -> DocumentParseResult:
        try:
            from docling.document_converter import DocumentConverter  # type: ignore
        except Exception as exc:
            return DocumentParseResult(
                status="missing_dependency",
                path=str(path),
                suffix=path.suffix.lower(),
                blocks=[],
                text="",
                parser="docling",
                error=f"Docling is required to parse {path.suffix.lower()} files: {exc}",
            )

        try:
            conversion = DocumentConverter().convert(str(path))
            document = conversion.document
            text = document.export_to_markdown()
            return DocumentParseResult(
                status="ok",
                path=str(path),
                suffix=path.suffix.lower(),
                blocks=self._text_blocks(text),
                text=text,
                parser="docling",
            )
        except Exception as exc:
            return DocumentParseResult(
                status="error",
                path=str(path),
                suffix=path.suffix.lower(),
                blocks=[],
                text="",
                parser="docling",
                error=str(exc),
            )

    @staticmethod
    def _text_blocks(text: str) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        for index, block in enumerate(re.split(r"\n\s*\n", text.strip())):
            content = block.strip()
            if content:
                blocks.append({"type": "text", "index": index, "content": content})
        return blocks
