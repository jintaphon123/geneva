---
name: notebooklm
description: Programmatic access to Bond's Google NotebookLM notebooks. Query notebooks, add sources, generate content. Activate on /notebooklm or intent like "ถาม NotebookLM", "query notebook", "add source to notebook".
---

# NotebookLM Skill — Bond's MyBrain Integration

CLI: `~/bin/notebooklm` (venv at `~/.notebooklm-venv`)
Registry: `references/notebooklm-registry.md` — read this to find notebook IDs

---

## Routing Logic

Before querying, read `references/notebooklm-registry.md` to find the right notebook ID.

```
export PATH="$HOME/bin:$PATH"
```

Always prepend this before running notebooklm commands in bash.

---

## Core Commands

| Task | Command |
|--|--|
| List notebooks | `notebooklm list` |
| Set active notebook | `notebooklm use <notebook_id>` |
| Query notebook | `notebooklm ask "question"` |
| Query specific notebook | `notebooklm use <id> && notebooklm ask "question"` |
| Add URL/file source | `notebooklm source add "url_or_path"` |
| Add web research | `notebooklm source add-research "query"` |
| Deep web research | `notebooklm source add-research "query" --mode deep --no-wait` |
| List sources | `notebooklm source list` |
| Generate podcast | `notebooklm generate audio "instructions"` |
| Generate report | `notebooklm generate report --format briefing-doc` |
| Generate infographic | `notebooklm generate infographic` |
| Generate quiz | `notebooklm generate quiz` |
| Check auth | `notebooklm auth check` |
| Check artifact status | `notebooklm artifact list` |
| Download audio | `notebooklm download audio ./output.mp3` |
| Download report | `notebooklm download report ./report.md` |

---

## Querying a Specific Notebook

```bash
export PATH="$HOME/bin:$PATH"
notebooklm use <notebook_id>
notebooklm ask "your question here"
```

For multiple notebooks on the same topic, query each and synthesize:
```bash
notebooklm use <id_1> && notebooklm ask "question"
notebooklm use <id_2> && notebooklm ask "question"
# Then synthesize both answers
```

---

## Auth Recovery

If auth fails:
```bash
# Re-run login script (Bond must sign in manually)
source ~/.notebooklm-venv/bin/activate
notebooklm auth check
```

If still broken, delete profile and re-authenticate:
```bash
rm -rf ~/.notebooklm/browser_profile ~/.notebooklm/storage_state.json
# Then run the login script from NotebookLMSkill setup
```

---

## Autonomy Rules

**Run automatically (no ask):**
- `auth check`, `list`, `use`, `source list`, `artifact list`, `status`, `ask`

**Ask before running:**
- `generate *` — long-running, may fail
- `download *` — writes to filesystem
- `source add` — modifies notebook
- `delete` — destructive

---

## Notes for Bond's System

- Web research (`add-research`) runs on Google's servers — near-zero token cost
- Content generation (podcast, infographic, quiz) is free in NotebookLM
- Thai queries work but English queries tend to be more precise
- Bond AI Brain ID: `664fde45-bda9-4072-85ec-27ed2cbd15f5`
