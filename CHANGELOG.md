# Changelog

All notable changes to Geneva are documented here.

Format: [Semantic Versioning](https://semver.org) — `MAJOR.MINOR.PATCH`

---

## [0.1.0] — 2026-05-20

Initial open source release of Geneva Layer 0.

### Core runtime
- Interactive REPL (`geneva`) with streaming responses and slash commands
- FastAPI web server (`src/geneva/web_server.py`) serving local React UI
- Session management with compaction, title generation, and history

### Memory system
- SQLite FTS5 memory store with `ADD`, `SUPERSEDE`, `ARCHIVE` operations
- Temporal schema — memories carry confidence, scope, and source metadata
- Auto-dream consolidation service — background memory distillation after sessions
- Memory write review with conflict detection and user-approval gate
- Context disclosure strip — per-turn summary of what memory was injected

### Projects
- Project workspace with scoped sources (text, markdown, URL, PDF, DOCX)
- Research engine — multi-source deep research with durable `research_runs` and report artifacts
- Full-brain search across chats, projects, memories, sources, research reports

### Skills & plugins
- Markdown skill loader from `.geneva/skills/`, project `.geneva/skills/`, and system paths
- Plugin CRUD API with safety-status tracking
- Skill browser UI with live status, triggers, and one-click invocation

### Tools
- Code runner (Python, JavaScript, shell)
- Web fetch with trust-policy enforcement (`[UNTRUSTED SOURCE]` prefix)
- File I/O with path traversal protection
- Computer use adapter (Playwright) with safety gates
- MCP connector runtime (Google, Notion, GitHub adapters)

### Web UI (React/Vite/TypeScript)
- Chat canvas with streaming, artifacts panel, and research progress rail
- Cmd/Ctrl+K global search with grouped results and slash command center
- Project workspace view — sources tab, artifacts, research, skills, activity
- Memory browser — search, add, review conflicts, session memory timeline
- Settings — provider/model picker, API key management, CLI bridges, skill builder
- Responsive layout — mobile project bottom sheet, sidebar collapse

### Security & hardening
- Path traversal protection on all file-reading tools
- Atomic file writes with temp-file rename
- HTTP boundary enforcement on web server
- UUID race condition fix in session creation
- `assert` → `raise` migration in production paths

### Test suite
- 606 tests, 16 skipped, 0 failures
- Coverage: memory ops, research engine, tool system, provider adapters, web API, computer use, MCP, skills

---

[0.1.0]: https://github.com/jintaphon123/geneva/releases/tag/v0.1.0
