#!/bin/bash
# Three-Brain Delegate — routes heavy implementation to Codex with ChatGPT fallback.
#
# Usage:
#   delegate.sh "Implement X in file Y. Rules: Z."
#   echo "spec" | delegate.sh            # pipe spec via stdin
#   delegate.sh "spec" < context.txt     # stdin = extra context appended
#
# Exit codes: 0=success, 1=usage error, 2=codex failed (fallback generated)

set -euo pipefail

# ── Collect task spec ────────────────────────────────────────────────────────

TASK=""
if [ $# -gt 0 ]; then
    TASK="$*"
fi

# Append stdin if available (e.g. piped context file)
if [ ! -t 0 ]; then
    STDIN_CONTENT="$(cat)"
    if [ -n "$STDIN_CONTENT" ]; then
        TASK="${TASK}${TASK:+$'\n\n'}${STDIN_CONTENT}"
    fi
fi

if [ -z "$TASK" ]; then
    echo "[delegate] Usage: delegate.sh '<task spec>' or pipe spec via stdin" >&2
    exit 1
fi

# ── Self-check ────────────────────────────────────────────────────────────────

_chatgpt_fallback() {
    local task="$1"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "[three-brain] ChatGPT fallback — paste this into ChatGPT (o4-mini+):"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat <<PROMPT

[TASK]
${task}

[OUTPUT]
Return complete file content only. No explanation. No markdown fences. No commentary.
PROMPT
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

if ! command -v codex &>/dev/null; then
    echo "[delegate] codex CLI not found" >&2
    _chatgpt_fallback "$TASK"
    exit 2
fi

# ── Route to Codex ───────────────────────────────────────────────────────────

PREVIEW="$(echo "$TASK" | head -c 100 | tr '\n' ' ')"
echo "[three-brain → codex] ${PREVIEW}..."
echo ""

# Run codex and capture exit code without exiting on failure (set -e workaround)
set +e
echo "$TASK" | codex exec --skip-git-repo-check
CODEX_EXIT=$?
set -e

# ── Handle result ────────────────────────────────────────────────────────────

if [ $CODEX_EXIT -eq 0 ]; then
    echo ""
    echo "[three-brain] Codex done (exit 0)"
    exit 0
fi

# Codex failed — detect if rate limit
echo ""
echo "[three-brain] Codex exited with code ${CODEX_EXIT}" >&2

# Rate limit signals: exit 429 or message contains "rate limit" / "quota"
_chatgpt_fallback "$TASK"
exit 2
