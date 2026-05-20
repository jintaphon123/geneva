from __future__ import annotations

import json
import re


def _json_container(value: object) -> dict | list | None:
    return value if isinstance(value, (dict, list)) else None


def extract_json_from_response(text: str) -> dict | list | None:
    """Extract a JSON object or array from an LLM response.

    Handles surrounding prose or markdown formatting. Returns None when no
    valid JSON can be extracted. Raises no exceptions.
    """
    if not isinstance(text, str):
        return None

    try:
        return _json_container(json.loads(text))
    except (json.JSONDecodeError, ValueError):
        pass

    stripped = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return _json_container(json.loads(stripped))
    except (json.JSONDecodeError, ValueError):
        pass

    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if match:
        try:
            return _json_container(json.loads(match.group()))
        except (json.JSONDecodeError, ValueError):
            pass

    match = re.search(r"\[.*\]", stripped, re.DOTALL)
    if match:
        try:
            return _json_container(json.loads(match.group()))
        except (json.JSONDecodeError, ValueError):
            pass

    return None
