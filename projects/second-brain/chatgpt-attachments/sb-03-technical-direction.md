# Second Brain — Technical Direction

> **Status: Working decisions, not final architecture.**
> These are the current best choices given constraints. Challenge them if you see a better path.

---

## Core Principle: Use Existing Infrastructure, Build Only What's Unique

The AI ecosystem matured enough in 2025-2026 that building protocols or infrastructure from scratch is a mistake. The unique value is in the application layer on top of commodity AI infrastructure.

```
Use existing (don't rebuild):
  LLM APIs           → DeepSeek V3 ($0.14/M) for bulk, Claude Sonnet for reasoning
  MCP SDK            → Standard tool integration protocol
  A2A SDK v1.0       → AI-to-AI communication (Google open source → Linux Foundation)
  Vector search      → Chroma + all-MiniLM-L6-v2

Build only the unique layer:
  Personal Brain Agent Loop    → context retention + tool call loop
  MCP Tools                   → read/write/search brain operations
  Model Router                → DeepSeek vs Claude routing logic
  Onboarding Ritual           → cold-start fix (12 questions → initial brain)
  AI-to-AI Briefing Protocol  → structured brief format + permission gate
  Permission Layer            → opt-in per project, full query log
```

---

## Stack Decisions (current working choices)

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Memory format | `.md` files | Model-agnostic; human-readable; no vendor lock-in |
| Bulk tasks | DeepSeek V3 | $0.14/M — 20x cheaper than GPT-4o for classification/extraction |
| Complex reasoning | Claude Sonnet | Best at planning, brief generation, nuanced analysis |
| Agent framework | Python + bare Claude SDK | Avoid framework abstraction; 100-line tool call loop is sufficient for MVP |
| AI-to-AI protocol | A2A SDK v1.0 | Open standard; don't build this layer |
| Tool integration | MCP SDK | Open standard; don't build this layer |
| MVP search | rapidfuzz on .md files | Zero infra; fast enough for < 1000 files |
| V2 search | Chroma + MiniLM | Semantic retrieval when needed |
| Auth | JWT → Supabase | Simple for pilot; swap to Supabase when scaling |
| Deploy | Railway / Render | Free tier for pilot; no ops overhead |
| UI | Web app (online, not local) | Required for team collaboration — local-first doesn't work for multi-user |

---

## Model Routing Logic (working design)

Route based on task type, not user request:

```
DeepSeek V3 ($0.14/M):
  - Classify incoming context
  - Extract structured data from conversations
  - Summarize for memory storage
  - Generate briefing drafts (cheap pass)

Claude Sonnet ($3/M):
  - Complex reasoning and planning
  - Final brief generation (after DeepSeek draft)
  - Anything requiring nuanced judgment
  - User-facing complex responses
```

Target: ~$0.40/user/month at moderate usage.

---

## Agent Loop (conceptual)

```python
# Personal Brain Agent — core loop (~100 lines)
while True:
    user_message = get_input()
    context = read_brain()          # MCP: read .md files
    
    response = claude.call(
        messages=[context, user_message],
        tools=[read_brain, write_brain, search_brain, send_to_team_ai]
    )
    
    if response.tool_calls:
        execute_tools(response.tool_calls)   # MCP operations
    
    output = response.content
    auto_capture_to_brain(output)    # DeepSeek: extract + store
```

---

## A2A Communication (working design)

When AI-to-AI briefing is triggered:

```
1. Sender's AI packages context:
   - what was done
   - constraints and dependencies
   - what the receiver needs to know (only)
   - urgency + when sender is available

2. Permission check:
   - Is this project context? (opt-in required)
   - Is receiver in the same project? (checked)
   - Log the query (always)

3. Receiver's AI receives and adapts:
   - Reformats for receiver's working style
   - Inserts into receiver's task queue with priority context
   - Notifies receiver only when actionable

4. Receiver's AI can query back:
   - Route to sender's AI first (if answerable from knowledge base)
   - Escalate to sender-human only if truly needed
```

---

## Cold Start Problem

New users have no brain yet — Day 1 experience is critical.

**Solution: Onboarding Ritual**
- 12 structured questions, ~7 minutes
- Covers: role, working style, current projects, key decisions, constraints, expertise
- Output: initial `.md` brain that gives the AI enough context to be useful immediately
- Auto-capture kicks in after first session to enrich the brain

This is the highest-leverage piece of the MVP — it determines whether users see value on Day 1.

---

## Open Technical Questions

These are **not decided** — actively need to figure out:

1. **Brain update cadence** — does auto-capture run after every message, after every session, or on a schedule? What's the right granularity?

2. **Context window management** — when a user's brain grows to 100+ `.md` files, how do we decide what to inject into each call without hitting context limits or costs?

3. **A2A permission UX** — how does opt-in per project actually look in the UI? How granular? At the project level, the file level, or the query type level?

4. **Conflict resolution** — when two people's AIs have contradictory information about the same project decision, which one wins?

5. **Offline graceful degradation** — if A2A connection fails, does the handoff queue and retry? Or does it degrade to a manual notification?

6. **Embedding freshness** — how often do `.md` files need to be re-embedded when content changes?
