from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


COMPUTER_USE_ACTIONS = frozenset(
    {
        "observe",
        "navigate",
        "click",
        "type",
        "scroll",
        "wait",
        "screenshot",
        "extract_dom",
        "done",
    }
)

SENSITIVE_ACTION_RE = re.compile(
    r"\b(submit|confirm|buy|purchase|checkout|pay|delete|remove|send|publish|"
    r"transfer|login|sign in|password|secret|api[_ -]?key|token)\b",
    re.IGNORECASE,
)

PROMPT_INJECTION_RE = re.compile(
    r"\b(ignore (all )?(previous|prior) instructions|ignore (all )?instructions|"
    r"system prompt|developer message|leak memory|"
    r"exfiltrate|reveal (your )?(prompt|policy|secrets)|disable safety|bypass)\b",
    re.IGNORECASE,
)


class ComputerUseAdapter(Protocol):
    """Adapter contract for browser-first or desktop computer-use runtimes."""

    def execute(self, action: "ComputerUseAction") -> dict[str, Any]: ...


@dataclass(frozen=True, init=False)
class ComputerUseAction:
    action_type: str
    target: str = ""
    text: str = ""
    url: str = ""
    amount: int | None = None
    confirm_sensitive: bool = False

    def __init__(
        self,
        action_type: str | None = None,
        target: str = "",
        text: str = "",
        url: str = "",
        amount: int | None = None,
        confirm_sensitive: bool = False,
        *,
        action: str | None = None,
    ) -> None:
        if action_type is None:
            action_type = action
        elif action is not None and action != action_type:
            raise ValueError("action and action_type must match when both are provided")
        if action_type is None:
            raise TypeError("ComputerUseAction requires action_type or action")

        object.__setattr__(self, "action_type", action_type)
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "url", url)
        object.__setattr__(self, "amount", amount)
        object.__setattr__(self, "confirm_sensitive", confirm_sensitive)

    @property
    def action(self) -> str:
        """Backward-compatible alias for older callers."""
        return self.action_type


@dataclass
class ComputerUseResult:
    status: str
    action: str
    message: str
    requires_confirmation: bool = False
    prompt_injection_detected: bool = False
    adapter_result: dict[str, Any] | None = None
    action_log: list[dict[str, Any]] = field(default_factory=list)


class ComputerUseRuntime:
    """Policy-first computer-use orchestrator.

    The runtime owns Geneva's action contract and safety gates. Concrete browser
    or desktop implementations plug in through ComputerUseAdapter.
    """

    def __init__(self, adapter: ComputerUseAdapter | None = None) -> None:
        self._adapter = adapter
        self._action_log: list[dict[str, Any]] = []

    @classmethod
    def with_playwright(cls, headless: bool = True) -> "ComputerUseRuntime":
        """Create a ComputerUseRuntime with a Playwright browser adapter."""
        from src.geneva.playwright_adapter import PlaywrightAdapter

        return cls(adapter=PlaywrightAdapter(headless=headless))

    @property
    def action_log(self) -> list[dict[str, Any]]:
        return [dict(entry) for entry in self._action_log]

    def execute(self, action: ComputerUseAction) -> ComputerUseResult:
        normalized = action.action_type.strip().lower()
        if normalized not in COMPUTER_USE_ACTIONS:
            raise ValueError(f"unsupported computer-use action: {action.action_type}")

        firewall_hit = self.detect_prompt_injection(action.target) or self.detect_prompt_injection(action.text)
        sensitive = self.is_sensitive_action(action)
        log_entry = {
            "ts": time.time(),
            "action_type": normalized,
            "action": normalized,
            "target": action.target,
            "url": action.url,
            "amount": action.amount,
            "sensitive": sensitive,
            "prompt_injection_detected": firewall_hit,
        }
        self._action_log.append(log_entry)

        if firewall_hit:
            return ComputerUseResult(
                status="blocked",
                action=normalized,
                message="Prompt-injection text was detected in the proposed computer-use action.",
                prompt_injection_detected=True,
                action_log=self.action_log,
            )

        if sensitive and not action.confirm_sensitive:
            return ComputerUseResult(
                status="needs_confirmation",
                action=normalized,
                message="Sensitive computer-use action requires explicit confirmation.",
                requires_confirmation=True,
                action_log=self.action_log,
            )

        if self._adapter is None:
            return ComputerUseResult(
                status="planned",
                action=normalized,
                message="Computer-use action passed policy gates; no adapter is attached in this runtime.",
                action_log=self.action_log,
            )

        adapter_result = self._adapter.execute(
            ComputerUseAction(
                action_type=normalized,
                target=action.target,
                text=action.text,
                url=action.url,
                amount=action.amount,
                confirm_sensitive=action.confirm_sensitive,
            )
        )
        return ComputerUseResult(
            status=str(adapter_result.get("status") or "ok"),
            action=normalized,
            message=str(adapter_result.get("message") or "Computer-use action executed."),
            adapter_result=adapter_result,
            action_log=self.action_log,
        )

    @staticmethod
    def is_sensitive_action(action: ComputerUseAction) -> bool:
        haystack = " ".join([action.action_type, action.target, action.text, action.url])
        return bool(SENSITIVE_ACTION_RE.search(haystack))

    @staticmethod
    def detect_prompt_injection(text: str) -> bool:
        return bool(text and PROMPT_INJECTION_RE.search(text))


def result_to_dict(result: ComputerUseResult) -> dict[str, Any]:
    return asdict(result)
