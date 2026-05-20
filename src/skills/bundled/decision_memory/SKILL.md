---
name: decision-memory
description: Extract and format decisions from conversation for storage in decisions/log.md
---

When invoked:
1. Scan conversation for decisions made (explicit or implied)
2. Format each as: | Date | Decision | Rationale | Status |
3. Flag any decision that conflicts with existing logged decisions
4. Output ready-to-append markdown rows

Target file: decisions/log.md
