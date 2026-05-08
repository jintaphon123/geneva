# SOP: File Triage — Audit & Route Misplaced Files

## When to Run
- Start of any session where unfamiliar files appear at root or wrong location
- When Bond drops new files into the repo without specifying where they belong
- Periodic audit (every 5–10 sessions)

## Checklist

1. **Scan root for unexpected files**
   - Expected at root: `CLAUDE.md`, `CLAUDE.local.md`, `README.md`, `.gitignore`, `.claude/`
   - Everything else → investigate

2. **Identify file type**
   - Context about Bond/work → `context/`
   - Project-specific notes → `projects/<project-name>/`
   - Rules for Claude behavior → `.claude/rules/`
   - Reusable skill prompts → `.claude/skills/`
   - Reference material / SOPs → `references/`
   - Completed or paused work → `archives/`
   - Decision records → `decisions/log.md`

3. **Route or ask**
   - If purpose is clear → move to correct location and note it
   - If purpose is ambiguous → ask Bond: "ไฟล์นี้ต้องการให้วางไว้ที่ไหน หรือใช้ทำอะไร?"

4. **Never delete without confirming**
   - Even if a file looks like a duplicate or draft — ask first
