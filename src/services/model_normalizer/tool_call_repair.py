from __future__ import annotations

import json
import re


def repair_tool_call_json(raw: str) -> dict | None:
    """Attempt to repair a malformed tool call JSON arguments string.

    Returns parsed dict on success, None if all repair attempts fail.
    Raises no exceptions.
    """
    if not isinstance(raw, str):
        return None

    try:
        result = json.loads(raw)
        if isinstance(result, dict):
            return result
    except (json.JSONDecodeError, ValueError):
        pass

    stripped = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    stripped = re.sub(r"\s*```$", "", stripped)
    try:
        result = json.loads(stripped)
        if isinstance(result, dict):
            return result
    except (json.JSONDecodeError, ValueError):
        pass

    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, ValueError):
            pass

    return None
