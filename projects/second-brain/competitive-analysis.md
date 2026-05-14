# Competitive Analysis — Second Brain / Agent Harness
อัปเดตล่าสุด: 2026-05-11 (merged จาก Compet 1 + Compet 2)

> **Source note:** Compet 1 = Claude Haiku 4.5 | Compet 2 = Claude Sonnet 4.6 High
> ทั้งสองใช้ prompt เดียวกัน ตอบคนละมุม ต้อง merge ถึงได้ภาพสมบูรณ์
> **Finding:** Haiku 4.5 ทำ strategic breadth ได้ดีกว่า; Sonnet 4.6 ทำ technical depth ได้ดีกว่า — เป็น empirical proof ของ Second Brain's model routing thesis

---

## Landscape Map

| Player | Category | Per-person AI | Active (acts) | Team Layer | Model-Agnostic | Thai-viable |
|--------|----------|:---:|:---:|:---:|:---:|:---:|
| **Bond's Second Brain** | AI Memory OS | ✅ | ✅ | ✅ | ✅ | ✅ |
| TwinMind | Personal AI | ✅ | Partial | ❌ | ❌ | ❌ |
| OpenHarness (HKUDS) | Agent harness (dev) | ❌ | ✅ | ❌ | ✅ | Partial |
| Taskade | Multi-agent collab | ❌ | ✅ | ✅ | ❌ | Partial |
| Notion AI | Knowledge wiki | ❌ | ❌ | ✅ | ❌ | Partial |
| Dust.tt | Team AI | ❌ | ✅ | ✅ | ❌ | Partial |
| Mem.ai | Note + memory | ✅ | ❌ | ❌ | ❌ | ✅ |
| Mem0 | Dev memory layer | ❌ | ❌ | ❌ | ✅ | ✅ |
| Letta/MemGPT | Agent memory | ❌ | ✅ | ❌ | Partial | ✅ |

**Top-right quadrant (per-person + active + team intelligence layer) = ว่างสมบูรณ์ ไม่มีคู่แข่งที่ fund แล้ว**

---

## คู่แข่งที่อันตรายที่สุด 4 ราย

### 1. OpenHarness (HKUDS) — Technical Twin ที่น่ากลัวที่สุด
- Architecture เหมือนกันแทบทุกอย่าง: `MEMORY.md`, markdown skills, model-agnostic, hook-based
- Ship v0.1.0 → v0.1.7 ใน 18 วัน — velocity สูงมาก
- **เหนือกว่าเรา:** 43+ tool integrations, open-source community momentum
- **จุดอ่อน:** CLI-only, ไม่มี team layer, ไม่มี business model, academic project
- **Threat:** MEDIUM-HIGH (ถ้า ship team layer = escalate ทันที)
- **กลยุทธ์:** study + reuse patterns ของเขา อย่าแข่งตรงๆ ด้าน tooling — แข่งที่ team intelligence layer

### 2. TwinMind — Threat: HIGH (Rising)
- Sequoia-backed, valuation $60M, seed $5.7M
- Personal AI ที่ฟังการสนทนาตลอดเวลา — context capture friction = zero
- **เหนือกว่าเรา:** Cold start UX ดีกว่ามาก — user ไม่ต้องพิมพ์อะไร แค่พูด
- **จุดอ่อน:** ไม่มี team layer, ต้องใช้ mic ตลอด (ขัด PDPA ไทย), ไม่ model-agnostic, เข้า Thai enterprise ไม่ได้
- **ความเสี่ยงหลัก:** ถ้า TwinMind ship team layer ใน 6 เดือน = threat tier ขึ้น CRITICAL ทันที

### 3. Taskade — Threat: MEDIUM
- YC-backed, multi-agent team collab ทำงานจริงอยู่แล้วตอนนี้ (SB ยังไม่มี)
- **เหนือกว่าเรา:** UI ดีที่สุดในกลุ่ม, free tier generous, live multi-agent
- **จุดอ่อน:** platform-locked, ไม่มี behavioral memory, ไม่มี AI-to-AI briefing, ไม่มี Knowledge Inheritance

### 4. Notion AI — Threat: MEDIUM
- 5M+ users, SOC2, hundreds of integrations, brand = enterprise standard
- **เหนือกว่าเรา:** Distribution, trust, integrations
- **จุดอ่อน:** อ่านได้แค่ document ไม่รู้ว่าคุณ "ทำ" อะไร ไม่มี Knowledge Inheritance เลย

---

## คู่แข่งที่แท้จริงที่สุด ≠ Software

**LINE + WhatsApp + Google Docs** คือ "good enough" ที่ฆ่า productivity startup ส่วนใหญ่

Pitch ต้องเปิดด้วย pain ไม่ใช่ feature:
> **"ทุกครั้งที่คนออกจากทีม ความรู้หายไปกับเขา — ทีมต้องเรียนรู้ผิดพลาดเดิมซ้ำๆ"**

ไม่ใช่: "เรามี AI ที่ model-agnostic และ cross-LLM"

---

## จุดที่เราเหนือกว่าทุกคน (Unique Combination)

| Differentiator | ใครทำอยู่ |
|----------------|-----------|
| AI Communication Bridge — AI brief ทีมแทนคุณ | ไม่มีใคร |
| Knowledge Inheritance — พนักงานใหม่ = expert ทันที | ไม่มีใคร |
| AI-to-AI cross-person query network | ไม่มีใคร |
| Model-agnostic via .md files | Mem0/OpenHarness (dev-only เท่านั้น) |
| Per-person AI ที่ active + team layer | ไม่มีใคร |
| PDPA-compliant, Thai pricing, Thai language | ไม่มีใคร |

---

## จุดที่เราแพ้ทุกคน (ต้องแก้ก่อน pitch)

| จุดอ่อน SB | ใครชนะ |
|------------|---------|
| UX ยังไม่มี | ทุกคน |
| Multi-agent live ไม่ทัน | Taskade |
| Cold start friction สูง | TwinMind |
| Brand / Community = 0 | Notion, Taskade |
| Support = 0 | ทุกคน |

**Fix สำคัญ:**
- Progressive disclosure onboarding — ถาม 2-3 คำถามผ่าน conversation ไม่ใช่ form 12 ข้อ
- Demo AI Communication Bridge ใน Month 1 — นี่คือ feature ที่ไม่มีใครทำ
- KU pilot 14 วัน — Day-3 retention ≥60% = GO signal (metric หลัก 90 วัน)

---

## Battlecards (ใช้ทันที ทุก pitch)

```
vs Notion AI:  "Notion AI อ่านสิ่งที่คุณเขียน
                Second Brain รู้สิ่งที่คุณทำ แล้วส่งงานต่อทีมแทนคุณโดยอัตโนมัติ"

vs Taskade:    "Taskade agents ช่วยคุณทำงานเร็วขึ้น
                Second Brain agents ทำให้คุณไม่ต้อง brief กันอีกต่อไปเลย"

vs TwinMind:   "TwinMind ฟังคุณ — Second Brain ฟัง + จำ + ส่งต่อทีม"

vs ทุกคน:      "ทุกคนทำ individual tools — เราทำ organizational intelligence"
```

---

## Investor Signal

**NeoCognition raise $40M** = proof ว่า investors เชื่อ thesis เรา → ใส่ใน pitch deck ได้ทันที

---

## วิธีชนะ — 3 Moves

**Move 1: Win Thai enterprise ก่อน TwinMind เข้ามา**
- PDPA-compliant + local pricing (฿199/seat vs $20+) + Thai language = moat ที่ต่างชาติข้ามยาก

**Move 2: Ship AI Communication Bridge ก่อนใครในโลก**
- Feature นี้ไม่มีใครทำ — demo ให้ได้ใน Month 1 = unfair advantage ทันที

**Move 3: ใช้ KU teams เป็น living proof**
- Real usage data > slides ทุก pitch ทุกรอบ
- Day-3 retention data จาก 15-30 users = go/no-go signal

---

## Bottom Line

White space ยืนยันแล้ว — แต่ window ไม่กว้างไม่จำกัด

- **TwinMind** กำลังเดินมาหาเรา → ต้องมี working demo ก่อน 6 เดือน
- **OpenHarness** มี technical momentum สูง → reuse ไม่แข่ง
- **ความเสี่ยงหลักคือ execution speed + UX ไม่ใช่ feature gap**
- Day-3 retention ของ KU pilot คือ data ที่สำคัญที่สุดใน 90 วัน
