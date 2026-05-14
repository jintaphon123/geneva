# Second Brain — Master Roadmap

**Updated:** 2026-05-12
**Current Phase:** Phase 1 — กำลังดำเนินการ

---

## Phase 1 — Agent Harness Foundation
**เป้าหมาย:** สร้าง Python agent harness ที่สมบูรณ์เป็นฐาน พร้อม Memory Engine

**Base:** Clawd-Code (GPT-AGI, MIT, Python) — cloned ที่ `scratch/clawd-code/`

### สิ่งที่ทำ
4 AI agents ทำงาน parallel/sequential:

| Agent | หน้าที่ | รันเมื่อ |
|-------|---------|---------|
| AI 1A | state, hooks + Observation Masking, coordinator, MCP, cost, query/, server/ | ก่อน (parallel กับ AI 2) |
| AI 2 | brain_engine (จำ–ค้น–บริบท), memdir, autoDream, extractMemories, sessionMemory, teamSync, skills | ก่อน (parallel กับ AI 1A) |
| AI 1B | 22 commands, 15 tools, enhanced compaction, parity audit, wiring | หลัง AI 1A |
| AI A | review + fix imports + validate + wire ให้เป็น 1 ระบบ | หลังทุกตัว |

### Output
- Python harness ที่รันได้จริง มี 30+ tools, 22 commands, memory backbone
- brain_engine.py: `remember()` / `search()` / `refresh_context()` / `rebuild_index()`
- Observation Masking hook (ลด token 50%, performance ไม่ลด)
- Prompts: `.claude/plans/prompt-ai1a/1b/ai2/aia*.md`

---

## Phase 2 — Second Brain Core
**เป้าหมาย:** แปลง harness ให้เป็น Second Brain จริง — ลบ code tools, เพิ่ม memory + chat

### สิ่งที่ทำ
- **Strip** Claude Code features ออก (code execution, IDE integration, code-specific commands)
- **Memory System**
  - Temporal schema ใน .md frontmatter (created_at, confidence, expires_at)
  - SQLite FTS5 index บน memory vault (ผ่าน rebuild_index())
  - brain_engine v0.2: lifecycle (status transitions, retention cleanup)
- **Model Router:** DeepSeek V3 สำหรับ bulk → Claude Sonnet สำหรับ complex reasoning
- **Auto-memory:** extractMemories + autoDream ทำงานอัตโนมัติ — Bond ไม่ต้อง manual update
- **Chat Mode UI:** Streamlit (MVP, 1 วัน) → Next.js (production)

### Output
- Second Brain ที่คุยได้ผ่าน chat, จำข้าม session อัตโนมัติ
- ไม่มี terminal, ไม่มี IDE — ใช้ได้เลย
- ทดสอบกับ Bond เอง (dogfood ก่อน pilot)

**เกณฑ์ผ่าน:** Bond ใช้ Second Brain แทน Claude Code + MyBrain ได้โดยไม่รู้สึกขาดอะไร

---

## Phase 3 — Web Platform + KU Pilot
**เป้าหมาย:** ให้คนอื่นใช้ได้จริงผ่าน browser, วัด PMF

### สิ่งที่ทำ
- **Next.js Web App** — ChatGPT-like UI, ไม่มี technical complexity ให้ user เห็น
- **Auth + User Isolation** — JWT → Supabase, แต่ละ user มี brain ของตัวเอง
- **Onboarding Ritual** — progressive disclosure ผ่านการใช้งานจริง (ไม่ใช่ form)
- **Deploy:** Railway / Render (free tier สำหรับ pilot)
- **KU Pilot:** 3–5 ทีม Senior Project (15–30 users), 14 วัน

### PMF Metric
≥ 3/5 users กลับมาใช้เองใน Day 3 โดยไม่มีใครทวง = GO สู่ Phase 4

---

## Phase 4 — Platform Layer
**เป้าหมาย:** จาก productivity tool → OS สำหรับ AI

### สิ่งที่ทำ
- **Skill Store (App Store)**
  - Creator publish skills (free / paid)
  - Revenue split 70% creator / 30% platform
  - Skill security: opaque sandbox
- **Knowledge Marketplace (NotebookLM clone)**
  - Upload knowledge corpus → AI query จาก corpus เท่านั้น (no hallucination outside it)
  - Monetizable: ขาย knowledge pack
- **Team Brain**
  - Shared project memory (opt-in)
  - AI-to-AI handoff ผ่าน HTTP /query endpoint → A2A SDK v1.0
  - Knowledge Inheritance (คนใหม่เข้าถึงความรู้สะสม)
- **MCP Server**
  - Second Brain เป็น MCP server
  - Claude Desktop / Cursor / Cline / Windsurf เชื่อมต่อได้

---

## Phase 5 — Open Platform (Long-term Vision)
**เป้าหมาย:** ecosystem ที่คนอื่น build บน Second Brain ได้

### สิ่งที่อาจทำ
- **Code Repository** — GitHub-like สำหรับ AI-generated code (open / private / org mode)
  - AI ค้นจาก repository ก่อนสร้างใหม่ทุกครั้ง
  - อาจ partner กับ GitHub แทนสร้างเอง
- **Education B2G** — school email login, bulk token deal กับ MoE / school networks
- **Open AI Access** — free tier กับ skill ecosystem ครบ (monetize ผ่าน marketplace)
- **Enterprise** — Institutional Memory, AI Network query, succession planning

---

## Timeline (ประมาณ)

```
ตอนนี้         Phase 1: รัน 4 AI agents (Bond ตัดสินใจเมื่อพร้อม)

หลัง Phase 1   Phase 2: ~1–2 สัปดาห์ (strip + memory + Streamlit)
               Phase 3: ~1–2 สัปดาห์ (Next.js + auth + pilot launch)
               — KU pilot: พ.ค.–มิ.ย. 2026 —

ถ้า pilot ผ่าน Phase 4: ~1–2 เดือน (Skill Store + Team Brain)
               Phase 5: 6–18 เดือน (ecosystem scale)

Target: KU pilot ก่อนปิดเทอม ~14 มิ.ย. 2026
```

---

## สิ่งที่ Second Brain ต้องดีกว่า Claude Code + MyBrain เพื่อให้ Bond ย้าย

- [ ] จำข้าม session อัตโนมัติ (ไม่ต้องบอกให้อัปเดตไฟล์)
- [ ] เปิดแชทใหม่แล้ว context ยังอยู่ครบ
- [ ] ค้นหา memory ได้ทันทีด้วย `/memory search`
- [ ] model ตอบดีขึ้นจริงๆ เพราะมี context ที่ถูกต้อง
- [ ] UI ใช้งานได้โดยไม่ต้องเปิด terminal เลย
