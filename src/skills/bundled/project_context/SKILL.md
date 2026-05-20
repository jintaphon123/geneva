---
name: project-context
description: Load and summarize all relevant project context files for a named project
---

When invoked with project name:
1. Read projects/<name>/context.md
2. Read projects/<name>/log.md (last 5 entries)
3. Read projects/<name>/BUILD.md if exists
4. Synthesize: current status, key decisions, next actions
5. Flag any stale priorities or missed deadlines

Output: 1-page brief ready for immediate work start.
