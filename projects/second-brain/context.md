# Second Brain — Project Context

## Status
**Active — Primary Focus**

## What It Is
A platform that gives every person their own AI — one that knows them deeply, remembers every decision they've ever made, and gets smarter the longer they use it. Built on `.md` files so it works with any AI model and never locks into one vendor.

When people in the same org use Second Brain, their AIs connect — handing off work, briefing each other, and querying each other's knowledge automatically. The result: the whole organization compounds intelligence together, not just each person in isolation.

## Core Thesis

**ทำไมมนุษย์ถึงวนซ้ำทั้งที่มี AI แล้ว?**

AI tools แต่ละตัวฉลาดขึ้นทุกปี แต่องค์กรยังทำผิดซ้ำเรื่องเดิม พนักงานใหม่ยังต้องเรียนรู้จากศูนย์ และคนเก่งออกไปแล้วความรู้ก็หายไปด้วย

Root cause คือเดิมมาตลอด: **ความรู้อยู่ในหัวคน ไม่ใช่ในระบบ**

AI ยุคนี้ทำให้คนทำงานได้เร็วขึ้น แต่ไม่ได้แก้ว่าความรู้นั้นจะส่งต่อและสะสมยังไง คนยังต้องเขียน status update ยังต้อง brief ทีม ยังต้องนั่ง meeting เพื่ออธิบายสิ่งที่ AI รู้อยู่แล้ว

Second Brain แก้ที่ root cause: ดึง knowledge ออกจากหัวคนใส่ระบบที่สะสมและส่งต่อได้ — ไม่ใช่แค่ให้แต่ละคนทำงานเร็วขึ้น แต่ให้ทั้งองค์กรฉลาดขึ้นพร้อมกัน

**One For All:** พนักงานใหม่วันแรกเข้าถึงความรู้สะสมของทุกคนที่เคยทำงานที่นี่ก่อนหน้า คนที่ทำงานมา 5 ปีก็ได้รับ knowledge จากทุกคนในทีมต่อเนื่อง เหมือนพลัง One For All ที่ส่งต่อและขยายขึ้นทุกรุ่น — ไม่มีใครเริ่มจากศูนย์อีกต่อไป

## Key Differentiators
- **Personal Context Layer** — AI รู้ว่าคุณเป็นใคร ทำงานแบบไหน ตัดสินใจอะไรไปแล้ว context ไม่หายไปไหนเลย
- **AI Communication Bridge** — AI ของคุณรู้ทุก context ของงาน สื่อสารแทนคุณกับ AI ของทีมได้โดยอัตโนมัติ ไม่ต้องเขียน status update อีกต่อไป
- **Knowledge Inheritance** — พนักงานใหม่วันแรกเข้าถึงความรู้ของทุกคนที่เคยทำงานมาก่อน = expert from day 1 ไม่ต้องเริ่มนับหนึ่งใหม่
- **AI-to-AI Handoff** — ทีมส่งงานผ่าน AI โดยตรง ไม่ต้องนัด meeting เพื่อ brief กัน
- **Institutional Memory** — เมื่อคนออก ความรู้ยังอยู่ AI ยังตอบได้ บริษัทไม่เสียหายจากการลาออกอีก
- **AI Network** — query AI ของทุกคนในทีมพร้อมกัน เพื่อวิเคราะห์ performance, จัดทีม, หรือเรียนรู้จาก mistake ทั้งองค์กร
- **Model-Agnostic** — built on `.md` files; swap Claude, GPT, Gemini anytime — context เดินทางไปกับคุณ
- **Non-tech UI** — ChatGPT-level simplicity; terminal และ VS Code ล่องหนต่อผู้ใช้ปลายทาง

## Problem It Solves
- Knowledge walks out the door when people leave — บริษัทเสียหายทุกครั้งที่คนเก่งออก
- Organizations re-learn the same lessons over and over — ผิดพลาดซ้ำเรื่องเดิมข้ามปี ข้ามทศวรรษ
- Communication overhead กินเวลาคนเก่งหมด — แม้ใช้ AI ทำงานเร็วขึ้น แต่ยังต้องเสีย 20-40% ของวันไปกับ status updates, meetings, การอธิบายซ้ำสิ่งที่คนอื่นควรรู้แล้ว
- ยุค AI มาแต่องค์กรไม่ได้ก้าวหน้าจริง — AI tools แต่ละตัวฉลาดขึ้น แต่ knowledge ยังไม่สะสม เพราะไม่มีระบบที่เชื่อม AI ของแต่ละคนเข้าหากัน
- Repetitive, low-value work (documents, emails, forms) steals hours from every workday
- AI tools exist but require technical setup — most workers never benefit

## The Communication Layer

**โลกปัจจุบัน:**
```
Person A ทำงาน → A เขียน update → B อ่าน update → B ทำงาน
เวลาหาย: meeting, Slack thread, "ช่วยสรุปให้หน่อย", brief ซ้ำหลายรอบ
```

**Second Brain world:**
```
Person A ทำงาน → A's AI รู้ context ทั้งหมดแบบ real-time
→ A's AI สร้าง briefing ที่ถูกต้องสำหรับคนถัดไปโดยอัตโนมัติ
→ ส่งไปยัง B's AI ซึ่งรู้ว่า B กำลังทำอะไร deadline เป็นยังไง ต้องรู้อะไรบ้าง
→ B's AI วางแผนงานให้ B ตาม context ของ B เลย
ผลลัพธ์: zero redundant meetings, zero status updates, zero "ช่วยสรุปให้หน่อย"
```

---

**Scenario A — Work Handoff (ส่งงานข้ามคน)**
```
A (Designer) ทำ mockup เสร็จ

→ A's AI: อัปเดตแผนโปรเจกต์อัตโนมัติ + สร้าง briefing สำหรับ Dev
→ A's AI → B's AI (Dev):
   "mockup พร้อมแล้ว | ไฟล์อยู่ที่ [link] | constraint: mobile-first, font ห้ามเปลี่ยน
    A ว่างตอบคำถามได้วันพรุ่งนี้เช้า"

→ B's AI วิเคราะห์: B กำลัง focus งานอื่นอยู่ถึง 15:00
→ B's AI บอก B:
   "งานใหม่จาก A พร้อม | ตามแผน: เริ่มได้ 15:30 วันนี้
    step แรกคือ review constraint ใน [link] ใช้เวลา ~30 นาที
    ถ้ามีคำถามให้ถามผ่าน AI ก่อน A จะได้รับสรุปตอนเช้า"

ไม่มี meeting | ไม่มี Slack thread | ไม่มีใครต้องถามซ้ำ
```

**Scenario B — Cross-team Request (ขอความช่วยเหลือข้ามแผนก)**
```
C (Marketing) ต้องการ technical explanation สำหรับ pitch ลูกค้า

→ C's AI รู้ว่า C ต้องการ: non-tech language, 3 bullet, ภายในวันนี้
→ C's AI → D's AI (Engineer):
   "C ต้องการ explanation ของ feature X | non-tech audience | 3 bullet max
    urgency: ใช้วันนี้ 17:00 | ถ้า D ไม่ว่างบอกได้เลย"

→ D's AI ดึงจาก D's knowledge base ที่สะสมมา → draft คำตอบ
→ D's AI ส่งกลับ → C's AI แปลงให้อยู่ใน format ที่ C ต้องการ deliver

D ไม่ถูกรบกวนเลยถ้าคำถามตรงไปตรงมา
D รู้เรื่องนี้แค่ตอน review คำตอบก่อน approve (ถ้า D ต้องการ)
```

**Scenario C — Manager Query (ประเมินทีมแบบ real-time)**
```
Manager ต้องประเมิน performance ก่อนจัดทีมโปรเจกต์ใหม่

→ Manager's AI ส่ง query ไปยัง AI ของทุกคนในทีม
→ แต่ละ AI ตอบกลับด้วยข้อมูลจากการทำงานจริง:
   - งานที่ทำและ output จริง
   - decision ที่ตัดสินและผลที่ได้
   - ปัญหาที่เจอและแก้ยังไง
   - pattern การทำงาน: เร็วช้า, strong area, gap

→ Manager's AI synthesize ภาพรวม:
   "A: strong execution, weak cross-team comms
    B: best suited for project X ด้วย experience ใน domain นี้
    C: bandwidth ว่าง 60%, ready for new responsibility"

ไม่ต้องรอ quarterly review
ไม่ต้องนั่งจำว่าใครทำอะไรไป 3 เดือนที่ผ่านมา
```

## AI Network — Query & Evaluate

AI ของแต่ละคนไม่ได้ทำงานแยกกัน — มันเชื่อมกันเป็น network ที่ query ร่วมกันได้

**Performance Evaluation**
HR หรือ manager query AI ของพนักงานโดยตรง → AI ให้ข้อมูลจากการทำงานจริง ไม่ใช่ self-report ที่อาจ bias → ประเมินว่าควร promote, rotate, หรือ support ตาม evidence จริง

**Succession Planning**
เมื่อคนออก → AI ของเขายังอยู่ในระบบ → คนใหม่ที่มารับช่วงต่อ query AI ของคนเก่าได้แบบ interactive เหมือนนั่งคุยกับ predecessor โดยตรง ไม่ต้องเดาจาก document ที่ outdated

**Project Staffing**
ก่อนตั้งทีมโปรเจกต์ → Manager's AI query AI ของทุกคน → เห็นทันทีว่าใคร skill match, ใคร bandwidth ว่าง, ใครเคยผ่าน domain นี้มาแล้ว → จัดทีมได้แม่นยำโดยไม่ต้องนัด 1-on-1 ทุกคน

**Org-wide Learning**
เมื่อ mistake เกิด → ระบบ query AI ของทุกคนที่ connected กับ project นั้น → detect pattern ว่าเรื่องนี้เคยเกิดมาก่อนไหม เกิดจาก root cause อะไร → เสนอ fix ให้ทั้งองค์กรเพื่อไม่ให้เกิดซ้ำ

**ขอบเขตที่ AI ของแต่ละคนรับได้:**
- AI ของ A ถูก query ได้จาก: A เอง, Manager ของ A (ตาม permission), AI ของคนที่ทำงานร่วมกับ A
- ทุก query ถูก log ไว้ — A รู้ว่าใคร query อะไรไปบ้าง (transparency by design)
- ระดับ access กำหนดได้ตามบทบาทและ project

## Positioning (10-second answer)

**vs Notion AI:**
> "Notion AI อ่านสิ่งที่คุณเขียน — Second Brain รู้สิ่งที่คุณทำ ทั้งที่เขียนและไม่เขียน แล้วส่งต่องานแทนคุณโดยอัตโนมัติ"

Framing: Passive document knowledge (Notion) vs **Active behavioral intelligence** (Second Brain)

**vs Microsoft 365 Copilot:**
MS Copilot รู้ document ใน Microsoft ecosystem เท่านั้น; Second Brain รู้ behavior + ทำงานข้าม tools และข้ามคนได้โดยอัตโนมัติ

## Beachhead Market (Updated 2026-05-05)

**Phase 1: KU Senior Project / Capstone teams**
- Pain: ทีมลืม decision, handoff งานแย่, knowledge หายหลัง project จบ
- Access: Bond คือ target user — classmates อยู่ข้างๆ, zero cost
- Size: recruit 3-5 ทีม (15-30 users) สำหรับ validate
- Timeline: pilot พ.ค.-ก.ค. 2026

**Phase 2: KU Research Labs**
- อาจารย์ + นักศึกษา grad ที่ knowledge หายทุกครั้งที่ นศ. graduate

**Phase 3: Thai Startups (10-50 คน)**
- High growth = high onboarding pain = strong PMF signal

**Broader Market (long-term):**
Thai SME + องค์กรที่มี turnover สูง (agency, consulting, gov)

## Product Shape

- **UI:** Web app (ChatGPT-like) — **Online, not local** (required for team collaboration)
- **Memory:** Persistent `.md` context per user; MVP = Guided Onboarding Ritual (7 min, 12 Q→A สร้าง initial brain); auto-capture มาใน v2
- **Models:** Model-agnostic via MCP abstraction — **DeepSeek V3** ($0.14/M) สำหรับ bulk tasks, **Claude Sonnet 4.6** ($3/M) สำหรับ complex reasoning เท่านั้น → cost/free user ~$0.40/เดือน
- **Agent Harness:** Python + bare Claude SDK (tool call loop ~100 lines) + MCP SDK + A2A SDK v1.0
- **Protocols:** A2A v1.0 (open source, Google → Linux Foundation, เม.ย. 2026, SDK 5 ภาษา) สำหรับ AI-to-AI collab; ห้าม build protocol เอง
- **Search (MVP):** rapidfuzz บน .md files → Chroma + all-MiniLM-L6-v2 (Week 3+)
- **Auth:** Simple JWT → Supabase (production)
- **Deploy:** Railway / Render (free tier สำหรับ KU pilot)

## Agent Harness Architecture (Updated 2026-05-12)

### Build Tool vs Production Product (สำคัญมาก)

| Layer | คืออะไร | ใครเห็น |
|-------|---------|--------|
| **Build Tool** | Clawd-Code (MIT, Python) harness ที่ Bond ใช้ build/maintain Second Brain | Bond เท่านั้น |
| **Production Product** | Chat Mode agent — ChatGPT-like UI, ไม่มี terminal, ไม่มี code editor | End users |
| **MCP Server** | Second Brain เป็น MCP server ให้ Claude Desktop / Cursor / Cline เชื่อมต่อได้ | Power users (Phase 2+) |

### Foundation: Clawd-Code (Confirmed 2026-05-12)

```
Base: GPT-AGI/Clawd-Code (MIT license, Python 100%)
Location: scratch/clawd-code/
Has already: agent loop, 30+ tools, skill loader, multi-provider, compaction

4 AI agents build the missing subsystems in parallel:
  AI 1A (Foundation):  state, hooks, coordinator, MCP, cost, query/server
  AI 2  (Memory):      memdir, autoDream, extractMemories, sessionMemory, teamSync, skills
  AI 1B (Commands):    22 commands, 15 tools, parity audit, wiring → ต้องรอ 1A
  AI A  (Closer):      review + fix imports + validate → ต้องรอทุกตัว

Prompts: .claude/plans/prompt-ai1a/1b/ai2/aia*.md
```

### Production Architecture

```
Foundation (use existing — ห้าม rebuild):
  Clawd-Code (MIT Python)             → Agent loop, tools, skill loader base
  DeepSeek V3 API ($0.14/M)          → Bulk: classify, extract, summarize
  Claude Sonnet 4.6 ($3/M)           → Reasoning: planning, brief generation
  SQLite FTS5                         → Memory search + temporal queries
  A2A SDK v1.0 (Phase 2+)            → AI-to-AI protocol

Bond builds (unique layer only):
  Memory System (5-tier + temporal)  → Core/Episodic/Semantic/Procedural + substrate
  Code Repository                     → Persistent searchable knowledge assets
  Model Router                        → DeepSeek vs Claude routing logic
  Chat Mode UI                        → Streamlit → Next.js
  Skill/Knowledge Marketplace         → App Store for AI enhancements
  MCP Server Interface (Phase 2+)     → external tool integration
```

## PDPA Architecture

**"Bring Your Own Brain" model** — ผ่าน PDPC 2025-2026 AI guidelines:
- แต่ละ user เป็น **Controller** ของ data ตัวเอง (ไม่ใช่บริษัทเป็น Controller)
- Sharing = explicit opt-in ต่อ project — ไม่ใช่ auto-surveillance
- Skills แชร์ได้ by default; personal context ไม่แชร์เลย; project context = opt-in per project
- ทุก query ถูก log — เจ้าของเห็นว่าใคร query อะไร (transparency)

## Privacy Model

```
SHAREABLE (org-facing):
  Decision patterns, working style, domain knowledge, project decisions, problem-solving approach

PRIVATE (personal brain only — zero exposure):
  Personal info, colleague opinions, non-work conversations, marked-private content

TRANSPARENCY: ทุก query ถูก log — เจ้าของเห็นว่าใคร query อะไรไปบ้างตลอด
```

## Architecture Layers
```
Layer 0: Personal Brain (MVP — exists now)
  └─ .md + skills + context → model-agnostic, local-first
  └─ AI รู้จักเจ้าของแบบลึก: decision history, working style, expertise

Layer 1: Team Brain (Senior Project / Pilot target)
  └─ Shared org skills + shared decision history
  └─ AI-to-AI work handoff — ส่งงานข้ามคนโดยไม่ต้องมี meeting
  └─ AI Communication Bridge — AI brief ทีมแทนเจ้าของอัตโนมัติ

Layer 2: Institutional Memory (Commercial vision)
  └─ ทุก decision, style, expertise ของทุกคน → persist หลังออกจากบริษัท
  └─ AI Network — query ร่วมกัน, evaluate performance, detect pattern mistake
  └─ Org intelligence compounds กับทุก hire, decision, exit
```

## Business Model (Confirmed 2026-05-06)

| Tier | ราคา | Features | Cost to Bond |
|------|------|---------|-------------|
| **Free** | ฿0 | Solo AI companion, 30 interactions/วัน, DeepSeek routing only, .md brain ไม่จำกัด | ~$0.15/เดือน |
| **Starter** | **199 THB/เดือน** (~$5.50) | Unlimited interactions, basic collab invite | ~$0.50/เดือน |
| **Pro** | **699 THB/เดือน** (~$20) | Full: Claude Sonnet, AI-to-AI collab, skills sharing, unlimited memory | ~$0.80/เดือน |
| **Team** | **1,490 THB/seat/เดือน** (~$42) | Institutional Memory, team admin, shared project memory, AI brief automation | ~$1.20/seat/เดือน |

- **Pro ที่ ~$20** = benchmark เดียวกับ ChatGPT Plus / Claude Pro (premium positioning)
- **Starter 199 THB** = entry สำหรับ นักศึกษา / คนที่อยากลองก่อน (accessibility)
- **Upgrade trigger ที่ natural ที่สุด:** ช่วงแรกที่อยากใช้ AI-to-AI collab feature → paywall ตรงนั้น
- **Revenue path:** KU pilot free (M1) → 10 Founding Members 99 THB (M2) → 30 Pro + 1 Team (M3) → ~5,600 THB/เดือน

## KU Pilot Metrics (Confirmed 2026-05-06)

| Signal | เกณฑ์ |
|--------|-------|
| 🟢 PMF signal (GO) | ≥ 3/5 users กลับมาเองใน **Day 3** โดยไม่มีคนทวง |
| 🟡 Conditional | 2/5 กลับมา → แก้ onboarding ก่อน ยังไม่ pivot |
| 🔴 Pivot | 0-1/5 กลับมา Day 3 → job-to-be-done ผิด เปลี่ยน target user |

**Network effect warning:** Lagged — ต้อง hand-select และ onboard ทีละคน ห้ามพึ่ง viral growth จาก KU pilot

## Build Timeline (KU Pilot, Solo)

| Week | งาน | Deliverable |
|------|-----|------------|
| Week 1 (วันที่ 1-7) | Agent loop + MCP tools + Model router + Onboarding ritual | Solo brain ทำงานได้ |
| Week 2 (วันที่ 8-14) | Streamlit UI + Auth + onboard 5 KU users | 5 users ใช้งานจริง |
| Day 15-16 | วัด Day-3 retention | Go/No-Go for Week 3 |
| Week 3 (วันที่ 17-21) | A2A collab layer (ถ้าผ่าน) | AI-to-AI briefing ทำงาน |

## Current Stage
**Building MVP** → KU pilot (พ.ค.-มิ.ย. 2026) → Senior Project pitch → commercial

## Milestones

| Horizon | Goal |
|---------|------|
| 3 months (~ก.ค. 2026) | KU pilot ผ่าน Day-3 retention + A2A collab layer + Senior Project locked |
| 6 months (~พ.ย. 2026) | 5 Team deals, ~15,000-20,000 THB/เดือน revenue |
| 1 year (~พ.ค. 2027) | Commercial launch + Institutional Memory + AI running rental automation |

## Recruitment Strategy
- Built Claude Course dashboard to onboard Art + Soda onto shared AI learning
- Goal: shared learning → pilot experience → pitch Senior Project → co-founders committed
- Profiles: Bond (orange), Art (blue), Soda (green)

## Platform Vision — Second Brain as OS (2026-05-09)

### The iOS Analogy

Second Brain is not just a product — it is an **operating system for personal AI**.

```
┌─────────────────────────────────────────────────────────┐
│                    SECOND BRAIN OS                       │
├──────────────┬──────────────────┬───────────────────────┤
│  SKILL STORE │  KNOWLEDGE STORE │  COLLABORATION LAYER  │
│  (App Store) │  (Doc Marketplace│  (AI-to-AI network)   │
├──────────────┴──────────────────┴───────────────────────┤
│              RUNTIME ENGINE (hooks, tool runner)         │
├─────────────────────────────────────────────────────────┤
│         MODEL ROUTER (Claude / Gemini / DeepSeek...)     │
└─────────────────────────────────────────────────────────┘
```

Like iOS: runtime (agent harness) + distribution (Skill Store) + ecosystem (creator network).
iPhone ที่ไม่มี App Store ≠ iPhone ที่มี App Store — Second Brain ไม่มี ecosystem ≠ Second Brain ที่มี

### Skill Marketplace (App Store equivalent)

- Anyone can build and publish skills to the platform
- Three publishing tiers: **Free** / **Private** / **Paid**
- Paid options: one-time purchase (~฿19 per skill, price of one Apple song) OR **Subscription** (~฿100/month = unlimited skill usage)
- Subscription revenue distributed to creators proportional to usage
- Free skill creators also earn (smaller share) — incentivizes open contribution
- Skills are **opaque to buyers** (source not visible — security framework TBD)
- Revenue split: Creator 70% / Platform 30%

### Knowledge Marketplace

- Sell document/knowledge packages that enhance AI context
- Buyers attach to their brain; AI queries on demand (not full open access)
- Workflow: Doc AI monitors documents → summarizes relevant info → passes to Main AI
- Like NotebookLM but: monetizable, AI-to-AI queryable, integrated into live workflow
- Research mode: AI anchored only to your uploaded knowledge corpus — no hallucination outside it
- Sellers cannot be inspected by buyers (IP protected)

### Education & B2G

- School email login → free tier access for students
- Bulk token quota deals (school/government negotiates org-wide contract)
- Bond negotiates volume discount from Anthropic/Google/DeepSeek when usage scales
- Government partnership as distribution channel for digital literacy

### Platform Pricing Stack

| Tier | Price | Model |
|------|-------|-------|
| Free | ฿0 | Cheap model (DeepSeek/Qwen), limited quota |
| Individual | $5-10/month | Small quota but affordable for everyone |
| Premium | ~$20/month | Current Pro tier (Claude Sonnet level) |
| Education | B2G bulk deal | School/org negotiated per-token rate |

### Foundation Strategy — Open Source First (Updated 2026-05-12)

Foundation confirmed and cloned: **Clawd-Code (GPT-AGI/Clawd-Code, MIT, Python 100%)** at `scratch/clawd-code/`

- **Foundation:** Clawd-Code — working Python agent harness with 30+ tools, skill loader, multi-provider, compaction
- **Reference patterns (concept only, no code copy):** claude_code_clone (TypeScript), Hermes Agent, OpenHarness, agentmemory
- **Second Brain unique layer:** memory system (5-tier + temporal), Code Repository, skill/knowledge marketplace, AI-to-AI protocol
- **Web UI:** Chat Mode — Streamlit MVP → Next.js production (Phase 3)
- **Sequence:** Foundation (4 AI build) → Memory Layer → Chat UI → Code Repository → Marketplace

**What "enhance any AI model" means:**
Second Brain OS wraps any model (DeepSeek/Claude/Gemini) with persistent memory, skills, and context — the same model performs measurably better with Second Brain than without it. That is the product promise.

### Long-term: Open Platform

When platform has sufficient scale:
- Open AI access free (like ChatGPT free tier) but with skill ecosystem included
- Free users get: basic AI, free community skills, limited quota, cheap model routing
- Collaboration features available at free tier (limited seats)
- Monetization via: Skill Store cuts, Premium tiers, B2G contracts

---

## Code Repository — Knowledge Asset Layer (New Concept 2026-05-12)

ทุกสิ่งที่ AI สร้างใน session ไม่ควรหายไป — persist เป็น searchable asset ที่ใช้ซ้ำได้

### How It Works

```
User คุยกับ AI → AI สร้าง code/simulation/exercise/document
→ Auto-save ลง Code Repository พร้อม metadata (topic, language, source session)
→ ครั้งถัดไป: AI ค้น repository ก่อนสร้างใหม่
→ พบ? → adapt + customize → ไม่สร้างซ้ำ
→ ไม่พบ? → สร้างใหม่ + บันทึกเพิ่ม
```

### Visibility Modes

| Mode | ใคร access ได้ | ตัวอย่าง |
|------|--------------|---------|
| **Open** | ทุกคนในระบบ | Thermo simulation สำหรับนักศึกษา ME |
| **Team/Org** | เฉพาะ org/school ที่ upload | โจทย์ฟิสิกส์ของ Suankularb + เฉลย |
| **Private** | เจ้าของคนเดียว | โค้ดที่ Bond เขียนสำหรับงานส่วนตัว |

### Use Cases ที่ชัดเจน

- **Education:** นักเรียนเรียน Thermo → AI เขียน simulation → คนต่อไปใช้ต่อ adapt เป็น CFD (aerodynamics) → ไม่ต้องเริ่มใหม่
- **School/Org:** Suankularb upload โจทย์ฟิสิกส์ + เฉลย → AI ใช้เป็น reference ตอบนักเรียนได้ทันที → version ขั้นกว่าของ exercise sheet
- **Research:** Lab upload papers → AI ค้นจาก corpus นั้นก่อน (no hallucination outside corpus)
- **Team:** Code ที่ developer A เขียน → available ให้ developer B ใช้ต่อผ่าน AI ทันที

---

## Memory Architecture (Designed 2026-05-12)

### 5 Foundational Layers

```
┌─────────────────────────────────────────────────────┐
│  Layer 5: Agent Loop (runtime — Clawd-Code base)    │
├─────────────────────────────────────────────────────┤
│  Layer 4: MCP Interface (Phase 2+ — secondary)      │
├─────────────────────────────────────────────────────┤
│  Layer 3: Skill System (Procedural Memory)          │
│  .claude/skills/ (40 skills) — summary only in ctx  │
├─────────────────────────────────────────────────────┤
│  Layer 2: Memory Tiers                              │
│  ┌─────────────────────────────────────────────┐   │
│  │ Core (~2,000 tokens, always in context)     │   │
│  │ → me.md + current-priorities + active brief │   │
│  ├─────────────────────────────────────────────┤   │
│  │ Episodic (recent sessions, on demand)       │   │
│  │ → session-summary.md + recent decisions     │   │
│  ├─────────────────────────────────────────────┤   │
│  │ Semantic (retrieved by relevance query)     │   │
│  │ → memory/ files (19 ไฟล์ + growing)        │   │
│  ├─────────────────────────────────────────────┤   │
│  │ Procedural (skills — summary only in ctx)   │   │
│  │ → .claude/skills/ expand on invoke          │   │
│  └─────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────┤
│  Layer 1: Memory Substrate                          │
│  Markdown (.md) — portable, human-readable          │
│  SQLite FTS5 — keyword + temporal search            │
│  JSONL — session logs, episodic events              │
└─────────────────────────────────────────────────────┘
```

### Temporal Memory Schema (ทุก memory unit ต้องมี)

```yaml
---
name: Bond prefers Thai for brainstorming
type: feedback          # user | feedback | project | reference
created_at: 2026-05-12T14:30:00+07:00
last_validated_at: 2026-05-12T14:30:00+07:00
expires_at: null        # null = never; ISO date = expires then
confidence: 0.95        # 0.0-1.0; ลดเมื่อมีข้อมูลขัดแย้ง
source: session-xyz     # session ที่สร้าง
visibility: private     # private | team | org
---
```

**Staleness rules:**
- `last_validated_at` > 90 วัน + ยังไม่ expire → flag "possibly stale" → AI ถาม Bond ยืนยัน
- `expires_at` ผ่านแล้ว → archive อัตโนมัติ (ไม่ delete)
- `confidence < 0.5` → flag สำหรับ review

**Inspiration:** Letta/MemGPT (core/archival tiers, editable core), MemoryOS (L1/L2/L3 hierarchy + decay), Mem0/OpenMemory (MCP pattern สำหรับ external access)

---

## Open Questions
- Senior Project proposal deadline (TBD — confirm date ด่วน)
- NIA grant deadline รอบปัจจุบัน (ต้องหาก่อน)
- KU admin: มี budget authority ซื้อ software เองได้ไหม?
- Technical co-founder: Bond leads solo หรือ recruit ก่อน build?
- Apply **Anthropic Startup Program** ($10K credits) → **ทำก่อน build ทันที**
- **Skill security model: opaque skills sandbox อย่างไร — ป้องกัน malicious prompt injection**
- **Code Repository: open assets ที่ user contribute แล้ว IP เป็นของใคร? licensing model?**
- **Memory temporal: ถ้า confidence ลดลง → system alert หรือ silent archive?**
- ~~Open-source foundation~~ → **Resolved 2026-05-12:** GPT-AGI/Clawd-Code (MIT, Python) ✅
- ~~Privacy model~~ → **Resolved:** Bring Your Own Brain + explicit opt-in per project ✅
