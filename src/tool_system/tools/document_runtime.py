from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.geneva.document_runtime import DocumentRuntime

from ..context import ToolContext
from ..errors import ToolInputError, ToolPermissionError
from ..permission_handler import PermissionResult
from ..protocol import ToolResult
from ..registry import ToolSpec


class DocumentParseTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="DocumentParse",
            description="Parse a local document into structured blocks and extracted text.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "path": {"type": "string"},
                    "max_chars": {"type": "integer"},
                },
                "required": ["path"],
            },
            is_read_only=True,
            max_result_size_chars=100_000,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        path = _resolve_existing_path(tool_input.get("path"), context)
        max_chars = tool_input.get("max_chars", 50_000)
        if not isinstance(max_chars, int) or max_chars < 1 or max_chars > 100_000:
            raise ToolInputError("max_chars must be an integer between 1 and 100000")
        result = DocumentRuntime().parse(path)
        output = asdict(result)
        text = str(output.get("text") or "")
        if len(text) > max_chars:
            output["text"] = text[:max_chars] + "\n\n... [truncated] ..."
        context.mark_file_read(path)
        return ToolResult(name="DocumentParse", output=output)


class DocumentGenerateTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="DocumentGenerate",
            description="Generate a local markdown document from structured sections or markdown.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "output_path": {"type": "string"},
                    "title": {"type": "string"},
                    "markdown": {"type": "string"},
                    "sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": True,
                            "properties": {
                                "title": {"type": "string"},
                                "content": {"type": "string"},
                            },
                        },
                    },
                    "overwrite": {"type": "boolean"},
                },
                "required": ["output_path"],
            },
            is_read_only=False,
            is_destructive=False,
            max_result_size_chars=100_000,
        )

    def check_permissions(
        self,
        tool_input: dict[str, Any],
        context: ToolContext,
    ) -> PermissionResult:
        output_path = tool_input.get("output_path")
        if not isinstance(output_path, str):
            return PermissionResult.allow()
        try:
            path = context.ensure_allowed_path(output_path)
        except ToolPermissionError:
            return PermissionResult.allow()
        if path.suffix.lower() in {".md", ".markdown"} and not context.permission_context.allow_docs:
            return PermissionResult.ask(
                message="Writing documentation files is blocked unless allow_docs is enabled",
                suggestion="Enable allow_docs to generate markdown documents",
            )
        if path.exists() and bool(tool_input.get("overwrite")):
            return PermissionResult.ask(
                message="Overwriting an existing document requires confirmation",
                suggestion=f"Read the document first, then retry overwrite for {path}",
            )
        return PermissionResult.allow()

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        output_path = tool_input.get("output_path")
        if not isinstance(output_path, str) or not output_path.strip():
            raise ToolInputError("output_path must be a non-empty string")
        path = context.ensure_allowed_path(output_path)
        if path.suffix.lower() not in {"", ".md", ".markdown", ".txt"}:
            raise ToolInputError("DocumentGenerate currently writes markdown/plain-text outputs only")
        overwrite = bool(tool_input.get("overwrite"))
        if path.exists() and overwrite and not context.was_file_read_and_unchanged(path):
            raise ToolInputError("refusing to overwrite: document must be read first and unchanged since last read")
        sections = tool_input.get("sections")
        if sections is not None and not isinstance(sections, list):
            raise ToolInputError("sections must be an array when provided")
        result = DocumentRuntime().generate_markdown(
            output_path=path,
            title=str(tool_input.get("title") or "Untitled"),
            markdown=str(tool_input.get("markdown") or ""),
            sections=sections,
            overwrite=overwrite,
        )
        context.mark_file_read(path)
        verification = DocumentRuntime().verify(path)
        return ToolResult(
            name="DocumentGenerate",
            output={"document": asdict(result), "verification": asdict(verification)},
        )


class DocumentVerifyTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="DocumentVerify",
            description="Verify a generated document for existence, size, lines, and citation markers.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            is_read_only=True,
            max_result_size_chars=20_000,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        path = _resolve_path(tool_input.get("path"), context)
        result = DocumentRuntime().verify(path)
        if path.exists() and path.is_file():
            context.mark_file_read(path)
        return ToolResult(name="DocumentVerify", output=asdict(result))


def _resolve_path(value: object, context: ToolContext) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ToolInputError("path must be a non-empty string")
    return context.ensure_allowed_path(value)


def _resolve_existing_path(value: object, context: ToolContext) -> Path:
    path = _resolve_path(value, context)
    if not path.exists():
        raise ToolInputError(f"document not found: {path}")
    if path.is_dir():
        raise ToolInputError(f"path is a directory: {path}")
    return path
