from __future__ import annotations

import sqlite3
import zipfile
from pathlib import Path
from typing import Any

from src.geneva.events import TurnStreamEvent


def _patch_geneva_paths(monkeypatch: Any, tmp_path: Path) -> Path:
    db_path = tmp_path / "brain.db"
    monkeypatch.setenv("GENEVA_BRAIN_DB_PATH", str(db_path))
    monkeypatch.setenv("GENEVA_DATA_DIR", str(tmp_path / "data"))
    return db_path


def _write_docx(path: Path, text: str) -> None:
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>"
        f"{escaped}"
        "</w:t></w:r></w:p></w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        )
        archive.writestr("word/document.xml", document_xml)


def _write_pdf(path: Path, text: str) -> None:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET"
    body = (
        "%PDF-1.4\n"
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        "3 0 obj << /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> "
        "/Contents 5 0 R /MediaBox [0 0 612 792] >> endobj\n"
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        f"5 0 obj << /Length {len(stream.encode('latin-1'))} >> stream\n"
        f"{stream}\n"
        "endstream endobj\n"
        "trailer << /Root 1 0 R >>\n"
        "%%EOF\n"
    )
    path.write_bytes(body.encode("latin-1"))


def test_text_and_markdown_sources_are_snapshotted_without_creating_memory(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    db_path = _patch_geneva_paths(monkeypatch, tmp_path)

    from src.geneva.project_sources import ProjectSourceStore

    store = ProjectSourceStore()
    source = store.add_text_source(
        project_id="project-1",
        title="Roadmap note",
        content="# Plan\n\nGeneva source text",
        source_type="markdown",
    )

    assert source["parse_status"] == "ready"
    assert source["source_type"] == "markdown"
    assert source["snapshot_path"]
    assert "Geneva source text" in store.read_snapshot(source["id"])

    listed = store.list_sources("project-1")
    assert listed["count"] == 1
    assert listed["sources"][0]["id"] == source["id"]

    with sqlite3.connect(db_path) as conn:
        memory_count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    assert memory_count == 0


def test_url_source_uses_fetcher_and_caches_snapshot(tmp_path: Path, monkeypatch: Any) -> None:
    _patch_geneva_paths(monkeypatch, tmp_path)

    from src.geneva.project_sources import ProjectSourceStore

    store = ProjectSourceStore()
    source = store.add_url_source(
        project_id="project-1",
        url="https://example.com/post",
        title="Example",
        fetcher=lambda url: f"Fetched page body from {url}",
    )

    assert source["parse_status"] == "ready"
    assert source["uri"] == "https://example.com/post"
    assert "Fetched page body" in store.read_snapshot(source["id"])
    assert source["metadata"]["fetched_at"]


def test_excluded_or_failed_sources_do_not_enter_context_preview(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _patch_geneva_paths(monkeypatch, tmp_path)

    from src.geneva.project_sources import ProjectSourceStore

    store = ProjectSourceStore()
    ready = store.add_text_source(
        project_id="project-1",
        title="Ready",
        content="This source is usable.",
        source_type="text",
    )
    excluded = store.add_text_source(
        project_id="project-1",
        title="Excluded",
        content="This source must not be injected.",
        source_type="text",
    )
    failed = store.add_text_source(
        project_id="project-1",
        title="Failed",
        content="This failed source must not be injected.",
        source_type="text",
    )
    store.update_source("project-1", excluded["id"], include_policy="exclude")
    store.update_source("project-1", failed["id"], parse_status="failed", parse_error="bad input")

    preview = store.context_preview("project-1")

    assert "This source is usable." in preview["preview"]
    assert "This source must not be injected." not in preview["preview"]
    assert "This failed source must not be injected." not in preview["preview"]
    assert preview["count"] == 1
    assert preview["sources"][0]["id"] == ready["id"]


def test_api_creates_lists_excludes_and_previews_project_sources(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _patch_geneva_paths(monkeypatch, tmp_path)

    from src.geneva.project_store import ProjectStore
    from src.geneva.web_api import JsonApiResult, dispatch_api_request
    from src.geneva.web_runtime import SessionManager

    manager = SessionManager.__new__(SessionManager)
    project = ProjectStore().create_project("Source Project")
    created = dispatch_api_request(
        manager,
        "POST",
        f"/api/projects/{project.id}/sources",
        payload={"source_type": "markdown", "title": "Spec", "content": "# Spec\nUseful context"},
    )

    assert isinstance(created, JsonApiResult)
    source_id = created.payload["source"]["id"]  # type: ignore[index]
    assert created.payload["source"]["parse_status"] == "ready"  # type: ignore[index]

    listed = dispatch_api_request(manager, "GET", f"/api/projects/{project.id}/sources")
    assert listed.payload["count"] == 1  # type: ignore[index]

    preview = dispatch_api_request(manager, "GET", f"/api/projects/{project.id}/sources/context-preview")
    assert "Useful context" in preview.payload["preview"]  # type: ignore[index]

    updated = dispatch_api_request(
        manager,
        "PUT",
        f"/api/projects/{project.id}/sources/{source_id}",
        payload={"include_policy": "exclude"},
    )
    assert updated.payload["source"]["include_policy"] == "exclude"  # type: ignore[index]

    excluded_preview = dispatch_api_request(manager, "GET", f"/api/projects/{project.id}/sources/context-preview")
    assert "Useful context" not in excluded_preview.payload["preview"]  # type: ignore[index]


def test_chat_events_attaches_project_source_blocks_to_session(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _patch_geneva_paths(monkeypatch, tmp_path)

    from src.geneva.project_sources import ProjectSourceStore
    from src.geneva.project_store import ProjectStore
    from src.geneva.web_runtime import ChatRequest, chat_events

    project = ProjectStore().create_project("Source Project")
    ProjectSourceStore().add_text_source(
        project_id=project.id,
        title="Spec",
        content="Source-only project context",
        source_type="text",
    )

    class CapturingSession:
        session_id = "capture-session"

        def __init__(self) -> None:
            self.project_context = ""
            self.source_blocks: list[Any] = []

        def set_project_context(self, context: str, project_id: str | None = None) -> None:
            self.project_context = context

        def set_project_source_context_blocks(self, blocks: list[Any]) -> None:
            self.source_blocks = blocks

        def chat_stream(self, *_args: Any, **_kwargs: Any):
            yield TurnStreamEvent(
                turn_id="turn_1",
                event_seq=0,
                type="turn_complete",
                data={"session_id": self.session_id, "response_text": "ok"},
                timestamp=0,
            )

    class CapturingManager:
        def __init__(self) -> None:
            self.session = CapturingSession()

        def get(self, *_args: Any, **_kwargs: Any) -> CapturingSession:
            return self.session

    manager = CapturingManager()
    list(chat_events(manager, ChatRequest("use source", project_id=project.id)))

    assert manager.session.source_blocks
    assert manager.session.source_blocks[0].source_type == "project_source"
    assert "Source-only project context" in manager.session.source_blocks[0].text


def test_pdf_and_docx_sources_parse_to_snapshots_without_creating_memory(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    db_path = _patch_geneva_paths(monkeypatch, tmp_path)

    from src.geneva.project_sources import ProjectSourceStore

    pdf_path = tmp_path / "brief.pdf"
    docx_path = tmp_path / "manual.docx"
    _write_pdf(pdf_path, "PDF source context")
    _write_docx(docx_path, "DOCX source context")

    store = ProjectSourceStore()
    pdf = store.add_document_source(project_id="project-1", path=pdf_path, title="Brief")
    docx = store.add_document_source(project_id="project-1", path=docx_path, title="Manual")

    assert pdf["source_type"] == "pdf"
    assert pdf["parse_status"] == "ready"
    assert "PDF source context" in store.read_snapshot(pdf["id"])
    assert pdf["metadata"]["parser"]

    assert docx["source_type"] == "docx"
    assert docx["parse_status"] == "ready"
    assert "DOCX source context" in store.read_snapshot(docx["id"])
    assert docx["metadata"]["parser"] == "docx-zipxml"

    preview = store.context_preview("project-1")
    assert "PDF source context" in preview["preview"]
    assert "DOCX source context" in preview["preview"]

    with sqlite3.connect(db_path) as conn:
        memory_count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    assert memory_count == 0


def test_failed_document_source_is_recorded_but_not_in_context(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _patch_geneva_paths(monkeypatch, tmp_path)

    from src.geneva.project_sources import ProjectSourceStore

    broken_pdf = tmp_path / "broken.pdf"
    broken_pdf.write_bytes(b"%PDF-1.4\nbroken")

    store = ProjectSourceStore()
    source = store.add_document_source(project_id="project-1", path=broken_pdf, title="Broken PDF")

    assert source["source_type"] == "pdf"
    assert source["parse_status"] == "failed"
    assert source["parse_error"]

    listed = store.list_sources("project-1")
    assert listed["count"] == 1
    assert listed["sources"][0]["id"] == source["id"]

    preview = store.context_preview("project-1")
    assert preview["count"] == 0
    assert "broken" not in preview["preview"]


def test_api_creates_pdf_source_from_file_path(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _patch_geneva_paths(monkeypatch, tmp_path)

    from src.geneva.project_store import ProjectStore
    from src.geneva.web_api import JsonApiResult, dispatch_api_request
    from src.geneva.web_runtime import SessionManager

    pdf_path = tmp_path / "brief.pdf"
    _write_pdf(pdf_path, "API PDF source context")

    manager = SessionManager.__new__(SessionManager)
    project = ProjectStore().create_project("Document Sources")
    created = dispatch_api_request(
        manager,
        "POST",
        f"/api/projects/{project.id}/sources",
        payload={"source_type": "pdf", "title": "Brief", "file_path": str(pdf_path)},
    )

    assert isinstance(created, JsonApiResult)
    assert created.payload["source"]["parse_status"] == "ready"  # type: ignore[index]
    assert created.payload["source"]["source_type"] == "pdf"  # type: ignore[index]

    preview = dispatch_api_request(manager, "GET", f"/api/projects/{project.id}/sources/context-preview")
    assert "API PDF source context" in preview.payload["preview"]  # type: ignore[index]
