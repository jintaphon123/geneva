---
name: skill-builder
description: Create a new custom Geneva skill interactively. Ask the user what the skill should do, collect requirements through simple questions, build the SKILL.md, and save it directly to My Skills using SkillSave. Trigger when user says 'create a skill', 'new skill', 'build a skill', 'make a skill', 'สร้าง skill', 'สร้างสกิล', 'ทำ skill', or when /skill_builder is invoked.
---

# Skill Builder

## Absolute Rules (NEVER break these)

1. **NEVER call AskUserQuestion tool** — it doesn't work in this environment. Ask all questions through regular text replies only.
2. **Ask ONE question per message** — never combine multiple questions in one reply.
3. **NEVER dump the SKILL.md template or documentation** — the user should never see raw markdown templates.
4. **NEVER explain what skill-builder is** — just start collecting information immediately.

---

## Interview Flow

When invoked, check the user's message:
- If the message **already describes what the skill should do** (e.g. contains a topic/description) → skip Q1, treat that as the answer, and ask Q2 next.
- If the message is just `/skill_builder` with no context → ask Q1 first.

**Q1 — Purpose** (skip if already answered in initial message):
Reply with just: "Skill นี้ควรทำอะไร? อธิบายสั้นๆ 1–2 ประโยค"

**Q2 — Trigger** (after Q1 is answered):
Reply with just:
"เรียกใช้ยังไง?
(a) พิมพ์ /ชื่อ เรียกเองเท่านั้น
(b) Auto — ให้ Geneva detect จาก context อัตโนมัติ"

If (b): ask as a follow-up: "ตอนไหน / คีย์เวิร์ดอะไรที่ควร trigger?"

**Q3 — Steps (optional)**:
Reply with just: "มีขั้นตอนพิเศษอะไรที่ Skill ควรทำไหม? (หรือพิมพ์ 'ข้าม')"

**Q4 — Name**:
Reply with just: "ตั้งชื่อ Skill ว่าอะไรดี? (lowercase, ขีดกลางได้ เช่น 'code-review')"

---

## After all 4 questions are answered

**Step 1:** Show a summary (text only, no markdown code blocks):

ชื่อ: [name]
ทำอะไร: [description]
Trigger: [/name หรือ auto: keywords]

**Step 2:** Ask: "สร้างเลยไหม?"

**Step 3:** If yes — call SkillSave with:
- `name`: the skill name from Q4
- `content`: the generated SKILL.md (frontmatter + body, following the template below)

**Step 4:** After SkillSave succeeds, reply: "✓ Skill '[name]' สร้างแล้ว! ไปดูได้ที่ My Skills เลย"

---

## SKILL.md to generate for SkillSave (internal template — never show to user)

```
---
name: [skill-name]
description: [specific trigger description — describes WHEN to invoke, e.g. "Trigger when user asks for X, wants to analyze Y, or says 'ช่วยทำ Z'"]
---

# [Skill Title]

[2–3 sentence overview]

## When to Use
[Specific trigger conditions]

## Steps
[Numbered steps the AI follows]

## Output Format
[What the response should look like]
```
