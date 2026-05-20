"""Playwright-backed browser adapter for Geneva Computer Use.

Import is lazy - if playwright is not installed, class instantiation raises
ImportError with installation instructions.
"""

from __future__ import annotations

import base64
from typing import Any

from src.geneva.computer_use_runtime import ComputerUseAction


class PlaywrightAdapter:
    def __init__(self, headless: bool = True, timeout_ms: int = 10_000):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise ImportError(
                "Playwright is required for Computer Use. "
                "Install with: pip install playwright && playwright install chromium"
            ) from exc

        self._pw_context = sync_playwright().__enter__()
        self._browser = self._pw_context.chromium.launch(headless=headless)
        self._page = self._browser.new_page()
        self._page.set_default_timeout(timeout_ms)

    def execute(self, action: ComputerUseAction) -> dict[str, Any]:
        try:
            return self._execute(action)
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def _execute(self, action: ComputerUseAction) -> dict[str, Any]:
        action_type = action.action_type.strip().lower()
        page = self._page

        if action_type == "navigate":
            page.goto(action.target or action.url, wait_until="domcontentloaded")
            return {"status": "ok", "url": page.url}

        if action_type == "click":
            page.click(action.target)
            return {"status": "ok", "selector": action.target}

        if action_type == "type":
            if action.target:
                page.fill(action.target, action.text or "")
            else:
                page.keyboard.type(action.text or "")
            return {"status": "ok"}

        if action_type == "scroll":
            delta = int(action.text or "500")
            page.evaluate(f"window.scrollBy(0, {delta})")
            return {"status": "ok"}

        if action_type == "wait":
            page.wait_for_timeout(int(action.text or "1000"))
            return {"status": "ok"}

        if action_type == "screenshot":
            screenshot = page.screenshot(type="png")
            screenshot_b64 = base64.b64encode(screenshot).decode("ascii")
            return {"status": "ok", "screenshot_b64": screenshot_b64, "format": "png"}

        if action_type == "extract_dom":
            content = page.content()
            return {"status": "ok", "html": content[:8000], "truncated": len(content) > 8000}

        if action_type == "done":
            self.close()
            return {"status": "done"}

        return {"status": "error", "message": f"unsupported playwright action: {action.action_type}"}

    def close(self) -> None:
        """Close browser and playwright. Call when done."""
        try:
            self._browser.close()
            self._pw_context.__exit__(None, None, None)
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
