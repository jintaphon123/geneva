from __future__ import annotations

from .persona_block import PERSONA_COMPACT, PERSONA_FULL, PERSONA_MINIMAL
from .response_contracts import CONTRACTS_COMPACT, CONTRACTS_FULL, CONTRACTS_MINIMAL
from .thinking_policy import THINKING_COMPACT, THINKING_FULL, THINKING_MINIMAL
from src.services.model_normalizer.capability_registry import classify_model_tier as _classify


def get_model_tier(model: str) -> str:
    """Return 'strong', 'medium', or 'weak' — delegates to capability_registry."""
    return _classify(model)


def build_cognition_block(model: str) -> str:
    """Assemble the Geneva cognition system prompt block for the given model.

    Returns empty string on any error so callers can safely skip injection.
    """
    try:
        tier = get_model_tier(model)
        if tier == "strong":
            parts = [PERSONA_FULL, THINKING_FULL, CONTRACTS_FULL]
        elif tier == "medium":
            parts = [PERSONA_COMPACT, THINKING_COMPACT, CONTRACTS_COMPACT]
        else:
            parts = [PERSONA_MINIMAL, THINKING_MINIMAL, CONTRACTS_MINIMAL]
        return "\n\n".join(p.strip() for p in parts if p and p.strip())
    except Exception:
        return ""
