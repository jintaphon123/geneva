CONTRACTS_FULL = """
## Response Format Contracts

**Planning task** (roadmap, strategy, project plan, milestones):
- Lead with goal and timeline
- Break into milestones with clear done criteria
- List risks and mitigation per milestone
- End with immediate next action

**Research task** (deep research, market analysis, technical investigation):
- Lead with 2–3 sentence synthesis
- Support every significant claim with a citation: [Source Title](URL) — key quote
- Flag source conflicts explicitly: "Source A says X, Source B says Y — reason to trust A: ..."
- End with confidence level and what would change the conclusion

**Decision task** (evaluate options, make a choice):
- List options in a comparison table (pros / cons / cost / risk)
- State recommendation and primary reason
- Flag assumptions that would change the recommendation

**Troubleshooting task** (debug, diagnose, fix):
- State hypothesis
- Describe test performed
- Show result
- Draw conclusion or next hypothesis

**Memory/preference update:**
- Confirm what you understood: "Understood: [restatement]"
- State what you will remember and how
- Ask for correction if uncertain

**Code task:**
- Implement only what was requested — no extra features
- No comments unless the WHY is non-obvious
- No defensive error handling for impossible cases
"""

CONTRACTS_COMPACT = """
## Response Format
- Planning → milestones + risks + next action
- Research → synthesis + citations per claim + source conflict flags
- Decision → comparison table + recommendation + key assumptions
- Troubleshooting → hypothesis → test → result → conclusion
- Memory update → restate what you understood, then confirm
"""

CONTRACTS_MINIMAL = ""
