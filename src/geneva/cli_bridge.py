from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 120


class CLIBridge:
    """Subprocess wrappers for Gemini CLI and Codex CLI."""

    def __init__(self, gemini_bin: str = "gemini", codex_bin: str = "codex") -> None:
        self.gemini_bin = gemini_bin
        self.codex_bin = codex_bin

    def gemini_ok(self) -> bool:
        return shutil.which(self.gemini_bin) is not None

    def codex_ok(self) -> bool:
        return shutil.which(self.codex_bin) is not None

    def status(self) -> dict[str, bool]:
        return {"gemini_ok": self.gemini_ok(), "codex_ok": self.codex_ok()}

    def gemini_query(
        self,
        prompt: str,
        file_contents: list[tuple[str, str]] | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> str:
        """Run Gemini CLI with prompt. file_contents = [(filename, text), ...]"""
        if not self.gemini_ok():
            raise RuntimeError("Gemini CLI not found. Install: https://cloud.google.com/sdk")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cmd = [self.gemini_bin, "-p", prompt]

            if file_contents:
                for fname, content in file_contents:
                    safe_name = Path(fname).name or "input.txt"
                    fpath = tmp / safe_name
                    fpath.write_text(content, encoding="utf-8")
                    cmd.append(f"@{fpath}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )

        if result.returncode != 0:
            logger.warning("Gemini CLI stderr: %s", result.stderr[:500])
        output = result.stdout.strip()
        if not output:
            raise RuntimeError(f"Gemini CLI returned no output. stderr: {result.stderr[:300]}")
        return output

    def codex_exec(self, spec: str, timeout: int = 300) -> str:
        """Run Codex CLI with a spec."""
        if not self.codex_ok():
            raise RuntimeError("Codex CLI not found")
        result = subprocess.run(
            [self.codex_bin, "exec", "--skip-git-repo-check", spec],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return result.stdout.strip() or result.stderr.strip()

    def should_use_gemini(self, total_text_length: int) -> bool:
        """Return True if content is large enough to warrant Gemini CLI."""
        return total_text_length > 40_000 and self.gemini_ok()


_bridge: CLIBridge | None = None


def get_bridge() -> CLIBridge:
    global _bridge
    if _bridge is None:
        try:
            from src.geneva.settings_manager import load_settings

            cfg = load_settings()
            _bridge = CLIBridge(gemini_bin=cfg.gemini_cli_path, codex_bin=cfg.codex_cli_path)
        except Exception:
            _bridge = CLIBridge()
    return _bridge
