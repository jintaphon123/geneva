from __future__ import annotations

import html
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


RUN_TIMEOUT_SECONDS = 30
UNSAFE_CODE_RUN_ENV = "GENEVA_ENABLE_UNSAFE_CODE_RUN"


@dataclass(frozen=True)
class CodeRunResult:
    ok: bool
    kind: str
    output: str
    error: str = ""
    language: str = ""


def run_code(language: str, code: str) -> dict[str, Any]:
    normalized = _normalize_language(language, code)
    if normalized in {"html", "htm"}:
        return _result(True, "html", code, language=normalized)
    if normalized == "svg":
        return _result(True, "html", _wrap_svg(code), language=normalized)
    if normalized == "css":
        return _result(True, "html", _wrap_css(code), language=normalized)
    if normalized in {"js", "javascript", "mjs"}:
        if not _unsafe_code_run_enabled():
            return _unsafe_disabled_result(normalized)
        return _run_process("node", "snippet.js", code, normalized)
    if normalized in {"py", "python"}:
        if not _unsafe_code_run_enabled():
            return _unsafe_disabled_result(normalized)
        return _run_process(sys.executable, "snippet.py", code, normalized)
    if normalized in {"sh", "bash", "zsh"}:
        if not _unsafe_code_run_enabled():
            return _unsafe_disabled_result(normalized)
        shell = shutil.which(normalized) or shutil.which("bash") or shutil.which("sh")
        if shell is None:
            return _result(False, "text", "", f"No shell runtime found for {normalized}.", normalized)
        return _run_process(shell, "snippet.sh", code, normalized)
    return _result(
        False,
        "text",
        "",
        f"Running {normalized or 'this language'} is not supported on this machine yet.",
        normalized,
    )


def _run_process(binary: str, filename: str, code: str, language: str) -> dict[str, Any]:
    if language in {"js", "javascript", "mjs"} and shutil.which(binary) is None:
        return _result(False, "text", "", "Node.js was not found.", language)
    with tempfile.TemporaryDirectory(prefix="geneva-run-") as tmp:
        path = Path(tmp) / filename
        path.write_text(code, encoding="utf-8")
        try:
            completed = subprocess.run(
                [binary, str(path)],
                cwd=tmp,
                capture_output=True,
                check=False,
                text=True,
                timeout=RUN_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or "") + (exc.stderr or "")
            return _result(
                False,
                "text",
                output,
                f"Code timed out after {RUN_TIMEOUT_SECONDS} seconds.",
                language,
            )
    output = (completed.stdout or "") + (completed.stderr or "")
    return _result(completed.returncode == 0, "text", output, language=language)


def _normalize_language(language: str, code: str) -> str:
    normalized = language.strip().lower().removeprefix("language-")
    if normalized:
        return normalized
    text = code.lstrip().lower()
    if text.startswith("<!doctype html") or text.startswith("<html"):
        return "html"
    if text.startswith("<svg"):
        return "svg"
    return "text"


def _wrap_svg(code: str) -> str:
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#f7f4ee}"
        "svg{max-width:100%;max-height:100vh}</style></head><body>"
        f"{code}</body></html>"
    )


def _wrap_css(code: str) -> str:
    escaped = html.escape(code)
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f"<style>{code}</style></head><body>"
        "<main><h1>CSS Preview</h1><p>This sample page is styled by the generated CSS.</p>"
        "<button>Example button</button><section><h2>Card</h2><p>Preview content</p></section>"
        f"<pre>{escaped}</pre></main></body></html>"
    )


def _result(
    ok: bool,
    kind: str,
    output: str,
    error: str = "",
    language: str = "",
) -> dict[str, Any]:
    return asdict(CodeRunResult(ok=ok, kind=kind, output=output, error=error, language=language))


def _unsafe_code_run_enabled() -> bool:
    return os.environ.get(UNSAFE_CODE_RUN_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def _unsafe_disabled_result(language: str) -> dict[str, Any]:
    return _result(
        False,
        "text",
        "",
        (
            f"Running {language} is disabled. Geneva only previews HTML, SVG, and CSS "
            f"unless {UNSAFE_CODE_RUN_ENV}=1 is set for this local server."
        ),
        language,
    )
