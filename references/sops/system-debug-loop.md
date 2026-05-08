# SOP: System Debug Loop

When any part of the Second Brain system breaks — wrong output, lost context, skill failure, bad prompt result — run this loop before doing anything else.

## Steps

1. **Identify what broke** — pinpoint the exact failure: which file, which skill, which prompt, which output
2. **Fix the root cause** — don't patch symptoms; fix the actual file, rule, or context entry
3. **Verify the fix works** — re-run the task or prompt that failed and confirm correct output
4. **Update the relevant file** — workflow, skill, context, or rule that caused the failure
5. **Continue with a stronger system**

## What counts as a failure

- Context lost between sessions (wrong/missing info in `context/`)
- Skill produces inconsistent or wrong output
- Prompt returns generic response instead of Bond-specific response
- Decision not logged to `decisions/log.md`
- Session ended without summary in `templates/session-summary.md`

## Key principle

Every failure is a system improvement opportunity. Don't just fix-and-forget — the fix must be written back into the system so it never happens again.
