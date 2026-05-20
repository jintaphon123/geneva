# Geneva — Personal AI Brain OS

> A local, model-agnostic AI runtime that knows who you are, remembers everything you build, and gets smarter with every session.

[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-606%20passing-brightgreen.svg)](tests/)

---

## What is Geneva?

Geneva is a **personal AI brain harness** — a local runtime that combines persistent memory, reusable skills, project context, and tool execution into a single workspace you own completely.

Unlike cloud AI products:
- **Your data stays local** — memory lives in `~/.geneva/` on your machine
- **Model-agnostic** — works with any provider: OpenRouter, Anthropic, OpenAI, Google, GLM
- **Skills you define** — markdown-based reusable workflows, not locked-in plugins
- **Grows with you** — every session compounds into structured memory

---

## Core Capabilities

| Layer | What it does |
|-------|-------------|
| **Memory** | SQLite FTS5 store — structured, searchable, temporal. Memories survive across sessions. |
| **Projects** | Scoped context — sources, research reports, session history per project |
| **Skills** | Markdown-defined reusable workflows loaded at runtime |
| **Tools** | Code runner, web fetch, file I/O, computer use (Playwright), MCP connectors |
| **Research** | Deep Research engine — multi-source, report artifacts, durable runs |
| **Search** | Full-brain search across chats, projects, memories, sources, research reports |

---

## Quick Start

**Backend + CLI:**

```bash
git clone https://github.com/jintaphon123/geneva
cd geneva
pip install -e .
geneva login       # set your API key
geneva             # launch interactive REPL
```

**Web UI (React):**

```bash
cd geneva-ui
npm install
npm run dev        # starts Python API on :8765 + Vite on :5176
```

**Run tests:**

```bash
pytest             # 606 tests, ~14s
```

---

## Layout

```text
Geneva/
├── src/
│   ├── geneva/          # Web API, memory, projects, settings, skills, research
│   ├── memdir/          # Durable memory store (SQLite FTS5)
│   ├── tool_system/     # Agent tools and tool registry
│   ├── command_system/  # Slash command engine
│   └── services/        # Model routing, auto-dream consolidation
├── geneva-ui/           # React/Vite/Tailwind web interface
├── tests/               # 600+ pytest tests
└── scripts/             # QA and audit helpers
```

---

## Configuration

Settings live in `~/.geneva/settings.json`. Key environment variables:

```bash
GENEVA_PROVIDER          # openrouter | anthropic | openai | google
GENEVA_MODEL             # any model ID your provider supports
GENEVA_WORKSPACE_DIR     # path to your workspace (default: ~/Documents/Geneva)
GENEVA_SKILLS_DIR        # custom skills directory
GENEVA_BRAIN_DB_PATH     # custom memory DB path
GENEVA_MAX_OUTPUT_TOKENS # token budget per turn
```

---

## Memory Architecture

Geneva uses a **file + SQLite hybrid** memory system:

- `~/.geneva/memories/` — structured memory rows (FTS5 indexed)
- `~/.geneva/sessions/` — session transcripts
- `~/.geneva/projects/` — per-project context, sources, research
- `~/.geneva/soul.md` — your identity contract (who Geneva is to you)
- `~/.geneva/BRAIN.md` — runtime contract (how Geneva behaves)

Memory operations: `ADD`, `SUPERSEDE`, `ARCHIVE` — no silent overwrite.

---

## Skills

Create a skill at `.geneva/skills/<name>/SKILL.md`:

```yaml
---
name: research-brief
description: Deep research on any topic, returns structured brief
---

Run a 4-phase research cycle...
```

Invoke with `/research-brief` in the REPL or web UI.

---

## Status

Layer 0 (personal brain harness) is **complete and hardened** — 606 tests passing, production-grade memory, research engine, skills runtime, project workspace, MCP connectors, computer use, and full React web UI.

Layer 1 (AI-to-AI collaboration protocol) is in validation — designed for teams where each member's AI can hand off context, brief collaborators, and query each other's knowledge. Coming soon.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](LICENSE).
