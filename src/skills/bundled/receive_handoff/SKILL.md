---
name: receive-handoff
description: Load a teammate's handoff file into your AI context. After loading, your AI knows everything the previous person's AI knew — ask it anything about the project state.
---

# Receive Handoff

You are loading context from a teammate's AI handoff into this session.

## Step 1: Get the handoff file

Ask the user:
"แนบไฟล์ handoff.md มาได้เลย หรือ paste เนื้อหาในนี้"

Wait for the file content.

## Step 2: Parse and internalize

Read the handoff file carefully. Extract:
- **Project name and goal**
- **All decisions and their reasons** — this is the most important part
- **Open items and blockers**
- **Non-obvious context** the sender flagged

## Step 3: Confirm loaded context

Respond with a brief confirmation:

```
✓ Handoff loaded — {project_name}

I understand:
- We are working on: {one sentence}
- Key decisions already made: {2-3 bullets with the WHY}
- Open items: {count} items
- Immediate blocker: {blocker or "none"}

Suggested starting point:
{the suggested first question from the handoff, rephrased as an action}

Ready. What would you like to work on first?
```

## Step 4: Be ready to answer "why"

After loading, you can answer questions like:
- "ทำไมเราถึงเลือก X?" → ตอบจาก decisions table ใน handoff
- "ตอนนี้ทำถึงไหนแล้ว?" → ตอบจาก open items
- "ต่อไปทำอะไร?" → ตอบจาก open items + suggested first question
- "มีอะไรที่ต้องระวัง?" → ตอบจาก context section

---

**Key principle:** The handoff file represents what your teammate's AI knew.
You now know the same things. Act accordingly — no need to ask them to re-explain.
