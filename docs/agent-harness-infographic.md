# 📊 Agent Harness Infographic (Detailed)

---
## 🎯 Goal
- **Unify** multiple LLM providers & tools under a single command‑line interface.
- **Persist** context & memory across sessions in plain‑text Markdown.
- **Enable** rapid prototyping of autonomous agents that can **plan**, **act**, and **learn**.

---
## 🧱 Architecture Layers
| Layer | Responsibility | Core Files |
|------|----------------|-----------|
| **Engine** | Parses user commands, routes to appropriate provider, manages conversation lifecycle. | `src/agent/conversation.py`, `src/agent/session.py` |
| **Memory** | Token‑aware, time‑stamped buffer; writes to `context/` Markdown files. | `src/runtime.py`, `src/memdir/__init__.py` |
| **Tool System** | Declarative wrappers (Bash, WebFetch, CodeExec, etc.) exposing safe actions. | `src/tool_system/loader.py`, `src/tool_system/tools/*.py` |
| **Provider Adapters** | Normalises APIs of Anthropic, OpenAI‑compatible, GLM, Minimax. | `src/providers/*.py` |
| **Command Registry** | Maps `!cmd` strings to Python callables; supports hot‑reload. | `src/command_system/registry.py`, `src/command_system/builtins.py` |
| **UI / CLI** | Interactive REPL, VS Code side‑panel, optional web server. | `src/cli.py`, `src/server/__init__.py` |
| **Persistence** | All state lives in `.md` files + a tiny SQLite for token‑counters. | `context/`, `src/memdir/sqlite_store.py` |

---
## 🔄 Typical Workflow
```mermaid
flowchart TD
    A[User input] --> B[CLI parses]
    B --> C{Command type}
    C -->|!set provider| D[Provider Adapter]
    C -->|!tool <name>| E[Tool System]
    C -->|!plan| F[Planner (LLM) generates sequence]
    D --> G[LLM generates response]
    E --> G
    F --> G
    G --> H[Memory layer stores context]
    H --> I[Render to UI]
    I --> A
```
1. **Parse** `!set provider=anthropic` → updates global provider.
2. **Plan**: `!plan "summarize research and email"` → LLM returns a list of tool calls.
3. **Execute** each call via the **Tool System** (e.g., `!webfetch <url>`).
4. **Store** every interaction in `context/` markdown (auto‑timestamped).
5. **Render** response back to the user.

---
## ⚙️ Key Features
- **Multi‑LLM Switching** – `!set provider=openai` with optional model flag.
- **Context Stack** – `!push <key>` / `!pop` to manage scoped memory.
- **Undoable Actions** – Every tool call emits a toast; clicking *Undo* reverts the markdown change.
- **Extensible Tools** – Add a new tool by creating `src/tool_system/tools/<name>.py` and registering in `loader.py`.
- **Local‑First** – No external DB; all data is plain Markdown, version‑controlled via Git.
- **Testing Harness** – `tests/test_agent_harness.py` validates planning → execution loops.

---
## 🚀 Getting Started
```bash
# 1️⃣ Clone & install deps (uv recommended)
git clone https://github.com/jintaphon/MyBrain.git
cd MyBrain/projects/second-brain/Geneva
uv sync

# 2️⃣ Run the REPL
uv run src/cli.py

# 3️⃣ Quick commands
!set provider=anthropic        # switch LLM
!tool bash "ls -la"           # run a shell command
!plan "research renewable energy market"   # let LLM plan actions
```

---
## 📚 Reference Docs (in‑repo)
- `docs/guide/SETUP_GUIDE.md`
- `docs/guide/TESTING.md`
- `src/agent/README.md` (internal design notes)

---
*All code licensed under MIT – see `LICENSE`.*