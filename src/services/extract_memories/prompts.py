from __future__ import annotations


def _render_transcript(transcript: list[dict]) -> str:
    lines: list[str] = []
    for turn in transcript:
        role = turn.get("role", "unknown")
        content = str(turn.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def build_extract_auto_only_prompt(transcript: list[dict], existing_manifest: str) -> str:
    return "\n".join(
        [
            "Review the transcript and identify durable memories worth saving.",
            "Only save facts the user stated or explicitly asked to remember. Do not save assistant self-descriptions as user identity.",
            "Classify findings as one of: user preference, project decision, architectural decision, feedback, repeated mistake, working style, constraint, reference knowledge.",
            "Return ONLY a JSON array. Each item must use this schema:",
            '{"type":"user|project|feedback|reference","content":"...","memory_kind":"identity|preference|project|decision|reflection|reference|skill|feedback","evidence_quote":"short quote","sensitivity":"public|private|restricted","validity_window_days":null}',
            "",
            "Existing memory manifest:",
            existing_manifest or "(empty)",
            "",
            "Transcript:",
            _render_transcript(transcript),
        ]
    )


def build_extract_combined_prompt(
    transcript: list[dict],
    existing_manifest: str,
    user_request: str | None,
) -> str:
    sections = [
        "Review the transcript and extract durable memories.",
        "Respect any explicit user request about what should be remembered.",
        "Only save facts the user stated or explicitly asked to remember. Do not save assistant self-descriptions as user identity.",
        "Return ONLY a JSON array. Each item must use this schema:",
        '{"type":"user|project|feedback|reference","content":"...","memory_kind":"identity|preference|project|decision|reflection|reference|skill|feedback","evidence_quote":"short quote","sensitivity":"public|private|restricted","validity_window_days":null}',
        "",
        f"Explicit request: {user_request or '(none)'}",
        "",
        "Existing memory manifest:",
        existing_manifest or "(empty)",
        "",
        "Transcript:",
        _render_transcript(transcript),
    ]
    return "\n".join(sections)
