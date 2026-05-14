# Second Brain — Project Intelligence Log

สะสม findings จากทุก skill session ที่เกี่ยวกับ Second Brain / AI OS
อ่านไฟล์นี้ก่อน session ใหม่ทุกครั้ง เพื่อไม่ต้อง re-derive context ซ้ำ

---

## 2026-05-11 — Competitive Analysis Merge (Compet 1 + Compet 2 → competitive-analysis.md)

### Summary
Merged outputs จาก 2 AI ที่วิเคราะห์คู่แข่งด้วย prompt เดียวกัน ทั้งสองตอบคนละมุม ไม่มีใครอ่านไฟล์ผิด แต่ต้องเอามารวมกันถึงจะสมบูรณ์

- **Compet 1:** ครอบคลุม memory/personal AI market — TwinMind (Sequoia $60M), Dust.tt, Mem0, Thai PDPA moat, 3-move strategy
- **Compet 2:** ครอบคลุม agent harness market — OpenHarness (direct technical twin), Taskade (multi-agent live), battlecards, NeoCognition $40M
- **Critical find จาก Compet 2:** OpenHarness (HKUDS) มี architecture เหมือน SB แทบทุกอย่าง (MEMORY.md + markdown skills + model-agnostic + hook-based) — ship v0.1.0→v0.1.7 ใน 18 วัน
- **Critical find จาก Compet 1:** TwinMind คือ highest threat ที่ Compet 2 ไม่พูดถึงเลย

Merged file: `projects/second-brain/competitive-analysis.md`

---

## 2026-05-11 — /competitive-intel: Competitor Landscape Teardown

### คู่แข่งหลัก (Tier 1 — Direct)

| ชื่อ | ทำอะไร | ความน่ากลัว |
|------|--------|------------|
| **Mem.ai** | AI note-taking + auto-org + multi-LLM memory | ปานกลาง — $40M raised แต่ community sentiment พัง |
| **OpenHarness (HKUDS)** | Open-source agent harness + personal agent "Ohmo" | สูง — architecture เหมือน SB ที่สุด (MEMORY.md, .md skills, model-agnostic, hook-based) แต่ไม่มี team layer |
| **Taskade** | AI workspace + multi-agent team collab | สูง — UX ดีที่สุด, YC-backed, multi-agent live แล้ว |
| **Obsidian + Claude MCP** | Local markdown vault + AI | ปานกลาง — community pattern ไม่ใช่ product |

### คู่แข่ง Indirect (ต้อง watch)

- **Notion AI Agents** — ใหญ่ที่สุด, brand ดีที่สุด; แต่อ่านได้แค่ document ไม่ใช่ behavior
- **NeoCognition ($40M seed, เม.ย. 2026)** — same thesis (institutional memory) แต่ enterprise-first; validates our market
- **Meta (Limitless acquisition)** — hardware + personal memory inside Reality Labs; 3-5yr threat

### SB ชนะที่ไหน (uncontested whitespace)

- **AI Communication Bridge** — ไม่มีใครทำ: AI brief ทีมแทนคน โดยอัตโนมัติ ข้ามคน ข้าม AI
- **Knowledge Inheritance** — ไม่มีใครทำ: พนักงานใหม่ = expert from Day 1 ผ่าน org memory
- **Model-agnostic + PDPA-first org intelligence** — top-right quadrant ว่างอยู่คนเดียว
- **A2A v1.0 first-mover** — ยังไม่มีใคร ship consumer/SME product บน A2A
- **ราคา Thai-market-friendly** — ฿199-1,490 vs Notion $20+/seat

### คู่แข่งเหนือกว่า SB ตรงไหน (honest)

- **Notion AI** — UX polish, integrations, SOC2, brand, distribution; ชนะทุก metric ยกเว้น innovation
- **Taskade** — multi-agent collab ที่ทำงานจริงแล้ว ตอนนี้ SB ยังไม่มี
- **OpenHarness** — developer trust + 43+ integrations, Slack/Discord/Telegram; velocity สูง (v0.1.0→v0.1.7 ใน 18 วัน)
- **ทุกคน** — UX, docs, support, brand — SB ยังไม่ exist ในมุมมองของ user

### Positioning ที่ถูกต้อง

```
SB ไม่ใช่ "better Mem" หรือ "better Notion"
SB คือ Layer ที่อยู่เหนือ Notion — organizational intelligence layer
ที่ Notion, Taskade, Mem ไม่เคยแตะเลย
```

### Action items

- เร่ง KU pilot Week 1 — Day-3 retention คือ data ที่สำคัญที่สุดใน 90 วัน
- ใส่ NeoCognition ใน fundraising deck — $40M validates thesis; ใช้เป็น market proof
- Watch OpenHarness GitHub weekly — adopt hook patterns แทน build เอง
- A2A first-mover angle — lock ใน Senior Project pitch ทันที

---

## 2026-05-06 — Full Validation Sprint (5 skills: /research-brief → /scenario-planner → /consult → /agent-architect + /llm-engineer → /gtm-advisor)

### Verdict: ✅ GO

### Key Findings จาก /research-brief
- Personal KB AI market: $1.36B (2024) → $11.87B (2033), CAGR 27.2%
- Enterprise KM: $23.2B (2025) → $74.22B (2034) — ใหญ่กว่า personal tier มาก
- **Limitless (Rewind AI) acquired by Meta ธ.ค. 2025 → consumer product ปิด** = signal ว่า standalone consumer "second brain" ตายแล้ว
- Thailand/SEA: **Zero local competitors** ยืนยัน 3 independent searches
- A2A Protocol (Google → Linux Foundation, เม.ย. 2025): open standard สำหรับ AI-to-AI — แต่ยังเป็น enterprise backend เท่านั้น; **consumer-facing personal AI-to-AI collab = white space**
- DeepSeek V3: $0.14/M input = **21× ถูกกว่า Claude Sonnet** → viable freemium economics
- Adoption barrier #1: Cold start problem (manual input required before value)

### Key Findings จาก /scenario-planner
- Pure B2B: Survivable แต่ PDPA sales friction, revenue 6-9 เดือนออกไป
- Pure B2C "social add-friends": ❌ Fatal — no moat, Big Tech convergence ตรง
- **Hybrid path ที่ถูกต้อง:** Solo onboarding (Week 1-2) → Collab layer (Week 3 ถ้า retain) → B2B Team (Post-KU)
- **PDPA fix:** "Bring Your Own Brain" — user เป็น Controller ตัวเอง; sharing = explicit opt-in ต่อ project
- Wildcard #1: Anthropic policy change → MCP abstraction layer = mitigation
- Wildcard #2: "Good enough trap" — Thai teams ใช้ LINE อยู่แล้ว → ต้องขายที่ pain ไม่ใช่ feature

### Key Findings จาก /consult (Strategic Verdict)
- **GO verdict** — 96/100 quality score, NopPongsatorn + Claude Independent analysis converge
- White space confirmed: AI-to-AI personal collab layer ยังไม่มีใครทำ (A2A ทั้งหมดเป็น enterprise backend)
- NB insight: B2Team first (KU teams) → organic B2C via network effects (ไม่ใช่ B2C first)
- Devil's Advocate flaw: Solo retention ก่อน collab คือ assumption ยังไม่ verified → ต้อง prove solo value ก่อน
- **Retention metric ที่ถูก:** ≥ 3/5 users กลับมาเองใน Day 3 (ไม่ใช่ 60% after 14 days)
- Network effect = **lagged** ไม่ใช่ instant อย่าง LINE → hand-select users, ห้ามพึ่ง viral

### Key Findings จาก /agent-architect + /llm-engineer
- **Agent Harness ดีกว่า Software Wrapper**: tool call loop → plan → execute → observe = quality gap ที่ Bond เคยประสบกับ Anti-Gravity
- **Stack สุดท้าย:** Python + bare Claude SDK tool loop (~100 lines) + MCP SDK + A2A SDK v1.0 + rapidfuzz → Chroma (Week 3+)
- **Model routing:** DeepSeek V3 ($0.14/M) สำหรับ 60-70% ของ requests; Claude Sonnet สำหรับ reasoning + brief generation
- **Cost:** ~$0.40/free user/เดือน ด้วย prompt caching = freemium viable ✅
- **Onboarding ritual:** 12 คำถาม → generates initial me.md + work.md + priorities.md + skills.md ใน 7 นาที = cold start fix
- **ห้าม build:** Auto-capture, vector DB, mobile app, admin panel, real-time sync, custom A2A protocol ใน Week 1-2
- **Prompt caching:** cache static system prompt (personal brain) = 40-50% cost reduction

### Key Findings จาก /gtm-advisor (Business Model)
- **Model:** Freemium → Subscription (ไม่ใช่ pay-as-you-go หรือ partnership-first)
- **Upgrade trigger ที่ natural:** ช่วงแรกที่อยากใช้ AI-to-AI collab → paywall ตรงนั้น (ไม่ใช่ rate limit)
- **Anthropic Startup Program:** Apply ก่อน build = $10K credits → KU pilot ฟรี
- **Revenue path:** M1=free, M2=99 THB Founding Members (10 users), M3=~5,600 THB/เดือน

### Pricing ที่ Lock (Updated: Bond ต้องการ ~$20 main tier)

| Tier | ราคา | หมายเหตุ |
|------|------|---------|
| Free | ฿0 | Solo brain, 30 interactions/วัน, DeepSeek only |
| Starter | 199 THB/เดือน (~$5.50) | Entry สำหรับนักศึกษา |
| **Pro** | **699 THB/เดือน (~$20)** | Premium = Claude Pro/ChatGPT Plus tier |
| Team | 1,490 THB/seat/เดือน (~$42) | Institutional memory |

### Actions ที่ต้องทำก่อน Build

1. **Apply Anthropic Startup Program** ($10K credits) — ทำเดี๋ยวนี้
2. **หา NIA grant deadline** — สัปดาห์นี้
3. **Confirm Senior Project proposal deadline** — ปักหมุด calendar

---

## 2026-05-04 — /research-brief + /consult + /ceo-advisor (AI OS Strategic Analysis)

### Key Research Findings

- **ตลาด Agent Framework รวมตัวแล้ว:** LangGraph, CrewAI, Microsoft Agent Framework (merged AutoGen+SK) = top 3; แข่งตรงๆ = ตาย
- **Linux Foundation AAIF (ธ.ค. 2025):** Anthropic MCP + Block goose + OpenAI AGENTS.md ร่วม standardize open protocols = protocol layer กำลังถูก commoditize
- **Local/on-premise gap:** 79% orgs ใช้ AI agents แต่ 1 ใน 5 มี mature governance; cloud-first platforms ทำ on-premise regulated deployments ไม่ได้เพราะ revenue model conflict
- **Window แคบลง:** Microsoft Azure Local + Apple Intelligence + Google Gemma เริ่ม enter local space — window ของ Bond ~18-24 เดือน ไม่ใช่ permanent
- **Thai consumers:** ต้องการ AI ที่ลด complexity ไม่ใช่ high-tech features (SCBX 2026)

### Strategic Decisions Made

| ประเด็น | การตัดสินใจ | เหตุผล |
|---|---|---|
| Beachhead (validation) | Bond himself + KU engineering students | Zero CAC; feedback loop สมบูรณ์; Senior Project pitch ได้ทันที |
| Beachhead (commercial) | Thai regulated professionals (legal/accounting) | On-premise + PDPA = Giants ทำไม่ได้; แต่ต้องรอ ≥ Q3 2026 |
| Primary moat | Data gravity ใน Second Brain (compounding Markdown knowledge) | ยิ่งใช้นาน ข้อมูลสะสม ย้ายยิ่งเจ็บ; local/Ollama คือ commodity |
| Entry advantage | Local/on-premise + zero data leak | จริงในระยะสั้น แต่ไม่ใช่ durability moat |
| Product design must-have | Auto-capture (conversation → Markdown) | Manual input = cold start problem = churn สูง |

### Recommendations (ลำดับ)

1. **เดือน 1 (พ.ค.):** Build MVP v0 สำหรับ Bond ใช้เอง — auto-capture + memory recall + cross-session context
2. **เดือน 2 (มิ.ย.):** 5 KU users ทดลอง 14 วัน วัด retention; หา 1-3 beta users ที่จ่ายจริง; pitch co-founders ด้วย real data
3. **เดือน 3 (ก.ค.):** Form KU team → submit Senior Project → apply NIA grant

### Capital-Free Resources ที่ต้องใช้

- Ollama (free), GitHub (free), Vercel free tier
- KU Innovation Hub / KU Startup Space — mentorship + co-working
- **NIA grant:** ฿200K-500K สำหรับ university-based innovation → หา deadline ก่อน
- DEPA grant: ฿50K-200K สำหรับ digital/AI startup
- KU Senior Project budget (ถามอาจารย์ที่ปรึกษา)

### Milestone Gate ก.ค. 2026

- ✅ GO: working prototype + 2+ co-founders + ≥3/5 users ยังใช้หลัง 14 วัน + Senior Project accepted
- ⚠️ PAUSE: prototype ยังไม่ work / ทีมยังไม่ได้
- ❌ PIVOT: ไม่มี user ที่ใช้จริงหลัง 2 เดือน → เปลี่ยน beachhead

### Co-Founder Pitch Narrative (one-liner)

> "เราสร้าง AI ที่จำทุกอย่างที่คุณรู้ — run บนเครื่องคุณ ไม่มีข้อมูลรั่ว — เริ่มที่ตัวเราเองก่อน แล้วขยายไปหาคนที่เจ็บปวดกว่านี้"

### Known Risks

1. **Window ปิดเร็ว:** Giants enter local inference — ต้อง build vertical domain lock-in ให้ทัน
2. **Cold start problem:** Second Brain ไม่มีคุณค่าถ้าไม่มีข้อมูล → auto-capture คือ critical feature ไม่ใช่ nice-to-have
3. **KU students ≠ paying users:** ใช้เป็น validation sandbox ได้ แต่ revenue proof ต้องมาจาก professional users

### What Would Change the Strategy

- ถ้า KU users churn ก่อน 14 วัน → pivot beachhead เป็น KU research students + thesis management (JTBD ชัดกว่า)
- ถ้า Microsoft/Apple ประกาศ full Thai language on-device ก่อน Q3 2026 → double down บน domain knowledge ให้เร็วขึ้น

---

## 2026-05-05 — Vision Pivot Analysis (co-founder discussion)

### Changes from 2026-05-04

- **Online confirmed:** เปลี่ยนจาก local-first → online เพื่อ enable team collaboration จริง
- **Beachhead confirmed:** KU Senior Project teams (4-6 คน/ทีม, 3-5 ทีม = 15-30 users)
- **Agent Harness approach:** Re-engineer architecture (ไม่ copy code) บน Claude SDK + MCP foundation
- **Positioning locked:** "Notion AI อ่านที่คุณเขียน — Second Brain รู้ที่คุณทำ แล้วทำแทน"
- **Privacy taxonomy:** behavioral = shareable, personal = private, all queries logged

### New Moat Assessment (post-online pivot)

| Moat | สถานะ |
|---|---|
| Local/privacy advantage | ❌ หายไป — online ลบออก |
| AI-to-AI Communication Protocol | ✅ genuine gap ในตลาดไทย |
| Institutional Memory data gravity | ✅ ยิ่งใช้นาน ยิ่งย้ายยาก |
| Thai market first-mover | ✅ MS/Google ไม่ optimize Thai SME |

### Open Questions (ยังไม่ได้ตอบ)

- "ต่างจาก Microsoft 365 Copilot ยังไง" — ต้องตอบได้ชัดเหมือนที่ตอบ Notion ได้แล้ว
- Revenue model: per-seat? per-team? freemium?
- ข้อมูลเก็บที่ไหน: Thailand server หรือ cloud ต่างประเทศ? (PDPA)
- Technical co-founder ที่ build web app + backend ได้

---

## 2026-05-05 — Phase 1: Market Reality Check (/research-brief)

### Key Market Realities

- **Consumer Second Brain is Dead:** Meta acquired Limitless in Dec 2025 and killed the consumer product. Big Tech native features (MS Copilot, Google Gemini, Apple Intelligence) are swallowing the standalone consumer market.
- **Enterprise/Team Layer is the Blue Ocean:** Broad Knowledge Management (KM) is a $23B+ market. "Knowledge Inheritance" and institutional memory are validated pains in the Thai business context, with zero local competitors currently.
- **Cold Start Problem is the #1 Blocker:** Users churn before reaching the 'value' threshold because they have to manually input data. Auto-capture is mandatory.
- **Moat = Data Gravity + Switching Cost:** Based on WHOOP precedent, the longer a team uses the platform and builds institutional memory, the harder it is to switch back to generic Copilots.
- **Known Risks:** PDPA compliance regarding employee behavioral data monitoring in Thailand could introduce severe B2B sales friction. Technical feasibility of seamless "Auto-capture" is still unproven.

### Next Steps & Decision Point
- Proceed to Phase 2 (`/scenario-planner` → `/consult`) to stress test the B2B Team/Enterprise positioning and validate the Thai beachhead strategy against PDPA constraints and technical risks.

---

## 2026-05-06 — Phase 2: Scenario Planner Stress Test

### Scenario A (B2B Team Edition) — Critical Flaws
- **PDPA Trap (Survivable):** Auto-capture of behavioral data triggers DPIA requirements. Fix: "Bring Your Own Brain" model — user is their own Controller; team layer uses only explicitly shared content. KU pilot framed as "educational research" is IRB-exempt.
- **No Legal Counsel (Real Risk):** Bond has no DPO. Mitigation: KU pilot = research exempt; DPA template needed before first paying B2B customer.
- **Cold Start in B2B = Fatal without fix:** Onboarding > 15 mins = no-go. Fix: "Guided Onboarding Ritual" (20 questions / 20 mins) to seed initial brain. Auto-capture comes in v2.
- **Big Tech Counterattack (12-18mo window):** Survivable because M365 Copilot penetration in Thai SME is still low. Window closes if Big Tech improves Thai language support before Bond has 10 paying customers.
- **Revenue Timeline Risk:** B2B sales cycle = 3-6 months. Bond has $0 income. Fix: Anthropic startup credits + NIA grant + small pilot fee from Day 1 to test willingness to pay.

### Scenario B (B2C "Add Friends" Network Edition) — Critical Flaws
- **Chicken-and-Egg Network Effect (Fatal):** 15-30 KU users ≠ critical mass for viral growth. No distribution budget = no growth beyond KU.
- **Value Prop vs. Free Tools (Weak):** Notion/Google Docs/Line are free. No specific "aha moment" found where Second Brain clearly beats a @tag in Notion.
- **Freemium Doesn't Convert (Structural):** ~2-5% conversion on consumer tools; 30 KU users = 0-1 paying user.
- **Big Tech Convergence (Fatal in pure B2C):** ChatGPT Teams, Notion AI memory, Google Gemini Workspace all closing the gap. No localization moat in pure B2C play.
- **PDPA lighter but still present:** AI-to-AI sharing requires explicit per-project consent to avoid matra 19-20 violation.

### Bond's Perspective (B2C Reframe — 2026-05-06)
> Bond's vision for B2C is NOT a generic collab app. It is: "Personal AI companion" (cheap/local model — DeepSeek/Qwen/Ollama) that knows you deeply. The killer differentiator is AI-to-AI collaboration — when Bond works with Ploen, Bond's AI talks directly to Ploen's AI. Shared context is explicit and permission-based (folder/permission structure decides what is shared vs. private — e.g., Skills are shareable, personal context is not). This is a use case that no current consumer AI offers: your AI, knowing YOUR context, negotiating and collaborating with someone else's AI on your behalf.

### Scenario Verdict
| | Scenario A (B2B) | Scenario B (B2C Pure) | Bond's B2C Reframe |
|---|---|---|---|
| Death Holes | Mostly Survivable | Mostly Structural/Fatal | Partially Survivable |
| Moat | Institutional Memory + Thai-first | Weak | AI-to-AI Protocol (Genuine Gap) |
| Revenue Path | Clear but slow | Unclear | Unclear but potentially viral |
| Big Tech Risk | 12-18mo window | Fatal | Lower — no one does AI-to-AI for individuals yet |

### Directional Decisions (from Phase 2)
- **Hybrid Path Selected (Pending /consult):** Start B2C/individual (KU pilot, zero sales cycle, PDPA simpler) → if retention ≥ 60% at 14 days → package as B2B "Team Brain" for Thai SME.
- **PDPA Architecture:** "Bring Your Own Brain" + explicit per-project sharing permission model. NOT surveillance-style auto-capture of all employee data.
- **Anthropic Dependency:** Model-agnostic abstraction layer (MCP standard) required from Day 1. Route cheap tasks to DeepSeek/Qwen/Ollama; reserve Claude for high-complexity reasoning. This also solves the cost-per-user problem at scale.

---

## 2026-05-11 — /competitive-intel (Full Landscape Teardown)

### Tier Map
- **Tier 1 Direct:** Mem.ai, TwinMind, Mem0 (developer-facing)
- **Tier 2 Adjacent:** Notion AI, Confluence AI, Slite, Guru, Tettra, Dust.tt
- **Tier 3 Infrastructure (watch):** Letta/MemGPT, Zep, Supermemory
- **Tier 4 Giants:** MS 365 Copilot, Google Workspace AI, Slack AI
- **Tier 5 Dead/Pivoted:** Rewind AI/Limitless → Meta $2B acquisition Dec 2025, product shut

### Key Findings

- **White space confirmed:** Personal + active + multi-person AI network = ZERO funded competitor. TwinMind is personal but passive (listens, doesn't act). Dust is active but org-level not personal. Nobody is building AI-to-AI for individuals.
- **TwinMind is the most dangerous competitor:** $5.7M Sequoia-backed, 30K users, ex-Google X, but — always-on mic = PDPA violation in Thailand enterprise; no team layer at all; M&A target (Meta paid $2B for Rewind in same category Dec 2025)
- **Mem.ai:** Solo-only, passive, stagnant funding, vendor-locked. No team product whatsoever. SEO dominance on "AI second brain" keywords is the only threat.
- **Mem0:** $24M Series A, 48K GitHub stars, developer infrastructure. Threat = someone builds Bond's vision on Mem0. Protection = Mem0 is infra, not product; Bond's AI Communication Bridge + AI Network is the layer on top.
- **Notion AI real weakness (G2 data):** Dead wiki problem at 100+ users, no automated content verification, champion-dependent adoption — if the Notion champion leaves, wiki collapses. Bond's behavioral capture + auto-brief solves this structurally.
- **Dust.tt:** Best org-level agent workspace but no personal per-user AI. €29/user — not SMB-accessible. Gap left open: AI-to-AI collab across individual people.

### Verified Advantages
| Advantage | Durability |
|-----------|-----------|
| AI Communication Bridge — nobody has shipped it | 12-18 months |
| Knowledge Inheritance (behavioral, not document) | 18-24 months |
| AI Network (cross-person query via A2A) | 12 months |
| Model-agnostic .md stack | Permanent (data gravity moat) |
| Thailand PDPA / SEA positioning — no funded competitor | 18-24 months |
| Price: Free → 199 THB → 699 THB undercuts all | Permanent at Thai pricing |

### Verified Risks
| Risk | Mitigation |
|------|-----------|
| Cold start worse than TwinMind (speech capture) | Progressive disclosure via conversation; onboarding ritual 12Q → brain in 7 min |
| Solo retention before team features deliver value | Day-3 intrinsic return metric; prove solo before A2A |
| Meta/Big Tech with same vision in 2-3 years | Build network effects + data gravity before window closes |
| "Good enough trap" (LINE + Google Docs) | Sell on pain (knowledge dies when people leave), not feature |

### Positioning Statement (Locked)
> "Notion AI อ่านที่คุณเขียน — Second Brain รู้ที่คุณทำ แล้วทำแทน"

### Strategic Conclusion
Real competition = behavior (LINE + Google Docs + WhatsApp), not a specific product. Window is 12-18 months before well-capitalized team ships team layer. Moat must be network effects + data gravity, not product features alone.

### Actions Added to Plan
- Build `/vs-notion` SEO page early — capture comparison searches before traction
- Monitor TwinMind GitHub + Twitter monthly for enterprise/team announcements
- Cold start: implement progressive disclosure via conversation — not 12-question form
- Knowledge Inheritance demo = the demo that sells: new KU team member gets expert-level context Day 1
- **B2C Reframe (Bond):** AI-to-AI personal collaboration is a genuine white space. No competitor currently lets "your AI" talk to "your friend's AI" with permission-based context sharing. This IS the B2C moat.

---

## 2026-05-13 — Product Polish Pass: Composer + Project Workspace

### Changes Implemented
- Composer `+` menu now owns Attach File, Add to Project, Use Skill, Deep Research, and Web Search.
- Standalone Deep Research button removed from main composer surface.
- Use Skill submenu no longer disappears when moving pointer into the submenu.
- Add to Project now supports attaching to existing projects, not only creating a new project.
- Voice input hidden by default behind `localStorage.secondBrain.voiceInput=1` until a reliable voice pipeline exists.
- Code-heavy conversations no longer push the chat layout horizontally; desktop/mobile overflow verified at 0.
- ProjectView now defaults to Goals + Project Chats; Project Info moved behind edit icon/modal.
- Added project-scoped sessions endpoint so ProjectView matches SQLite project association counts.
- Project context injection now says Project Goals + Project Operating Mode, not generic tasks.

### Verification
- `npx tsc --noEmit` — pass
- `npm run build` — pass
- `python -m py_compile src/second_brain/project_store.py src/second_brain/web_runtime.py src/second_brain/web_server.py` — pass
- `python -m pytest tests/test_second_brain_web.py tests/test_second_brain_services.py tests/test_second_brain_memdir.py --tb=short` — 26 passed
- Playwright on `http://127.0.0.1:8766`: no console errors, no horizontal overflow, project sessions endpoint returned IMPACT session.

### Still Not Done
- True AI-managed goal extraction is not finished. Current pass sets the UX/context foundation; next pass must add a model-backed extractor/updater that proposes or updates project goals after each project conversation.

---

## 2026-05-13 — Project + Memory Academic Upgrade

### Research Used
- Self-regulated learning in project/problem-based learning requires goal setting, monitoring, reflection, and sustained motivation across the project lifecycle.
- Academic goal-setting works best when goals are specific, attainable, close enough to act on, and paired with feedback.
- Zettelkasten-style academic workflows separate source/literature notes, permanent notes, and project notes; collection without processing becomes dead storage.
- RAG/memory literature emphasizes metadata, freshness, provenance, query control, and user-specific memory stores.

### Changes Implemented
- WebSearch no longer inserts `[web-search]` into the composer or visible user message.
- WebSearch is now a hidden turn option: the backend receives an instruction to use web search, while the user-facing chat stays clean.
- ProjectView now has a `Project Memory` panel next to Goals.
- Project-scoped memory capture added for decisions, sources, reflections, and personal context.
- Project stats now show Active goals, Chats, and Memories.
- MemoryPanel now prioritizes active project memories when a project is attached.

### Verification
- `npx tsc --noEmit` — pass
- `npm run build` — pass
- Playwright verified:
  - WebSearch pill appears without mutating textarea.
  - Sent request has no `[web-search]` prefix.
  - User bubble has no `[web-search]` prefix.
  - Project Memory panel renders.
  - Desktop/mobile horizontal overflow remains 0.

### Remaining Architecture Gap
- Backend AI goal/memory extraction is still missing because core backend files were locked this round. Next backend-enabled pass should add extractor events that propose project goals and project-scoped memories automatically after each turn.

---

## 2026-05-13 — Memory Persistence + Episodic Recall Upgrade

### Changes Implemented
- Every successful Second Brain web turn now writes an episodic memory after the agent loop finishes.
- Episodic memory stores user text, assistant text, and summarized tool results so closed conversations remain searchable later.
- Episodic memories are excluded from `MEMORY.md` to prevent prompt pollution; retrieval pulls them only when relevant.
- Thai and non-English memory search now has a LIKE fallback when SQLite FTS does not return matches.
- Session JSON saves are now atomic and preserve Unicode, reducing the risk of corrupt closed-chat history during crashes.
- Session IDs now include microseconds plus random entropy to avoid collisions from rapid new-chat creation.
- Slash-command chat turns now enter conversation history and save the session instead of bypassing transcript persistence.
- Auto Dream is now checked automatically after successful web chat turns; no manual trigger is required.
- Auto Dream now writes a persistent last-consolidated marker after success instead of using the transient lock as state.
- Auto Dream default fallback consolidates from episodic memories, not raw session JSON, so ghost-mode chat history cannot be extracted later by accident.
- Durable memory extraction now understands Thai signals such as `จำ`, `ชอบ`, `ห้าม`, `ตัดสินใจ`, `เดดไลน์`, and `กำหนดส่ง`.

### Critical Fix During Review
- Episodic memory originally still used fuzzy update behavior inherited from durable facts. That would allow two similar chat turns to overwrite each other. This was fixed so episodic memory is append-only except exact duplicate hash no-ops.

### Verification
- `PYTHONPATH=. /opt/anaconda3/bin/pytest tests/test_second_brain_memdir.py tests/test_second_brain_services.py tests/test_second_brain_web.py tests/test_agent_loop.py tests/test_repl.py tests/test_command_system.py tests/test_tool_system_tools.py tests/test_providers.py -q` — 176 passed
- `npm run build` in `scratch/clawd-code/sb-ui` — pass
- `python3 -m compileall src/second_brain src/memdir src/agent src/services` — pass

### Remaining Architecture Gap
- Auto Dream still needs a model-backed consolidation pass that turns noisy episodic clusters into higher-quality semantic/procedural memories instead of relying only on heuristic extraction fallback.
- Project-scoped AI goal extraction still needs to promote project decisions/reflections from episodic memory into project memory automatically.

---

## 2026-05-13 — Memory Control Plane + Model-Backed Auto Dream

### Changes Implemented
- Added memory detail/provenance API: `/api/memory/{id}` now returns the memory plus parsed `source_session_id`, `captured_at`, and latest memory event history.
- Memory Browser now has an Inspect action for every memory, including metadata grid, raw storage path, content, and event payloads.
- Memory Browser supports `episodic` type filtering and visible counts for active/episodic/feedback/project/deleted memory.
- Auto Dream can now call the session provider as an agent-backed consolidation pass and store durable JSON memories returned by the model.
- Auto Dream prompt now includes recent episodic memories and requires strict JSON output, reducing prompt drift and making automated memory writes testable.
- Project chats now pass `project_id` into `SecondBrainSession`, so durable extraction and episodic capture can preserve project scope.
- Project memory extraction now recognizes goal, next action, reflection, todo, source, and Thai project signals before writing scoped memories.
- Memory card action buttons were made always visible after visual QA found that hover-hidden actions looked clickable in accessibility but disappeared visually in the real modal.

### Critical Fix During Review
- The first visual pass showed the Inspect/Edit/Archive/Delete actions were too hidden on real screenshots after reload. This was fixed by making the action row visible, compact, and directly clickable on every memory card.
- Provenance parsing initially failed for normalized Markdown content where `Session:` and `Captured at:` were collapsed onto one line. Regex parsing now handles both original multiline and normalized content.

### Verification
- `PYTHONPATH=. /opt/anaconda3/bin/pytest tests/test_second_brain_services.py tests/test_second_brain_web.py tests/test_second_brain_memdir.py -q` — 44 passed
- `PYTHONPATH=. /opt/anaconda3/bin/pytest tests/test_second_brain_memdir.py tests/test_second_brain_services.py tests/test_second_brain_web.py tests/test_agent_loop.py tests/test_repl.py tests/test_command_system.py tests/test_tool_system_tools.py tests/test_providers.py -q` — 179 passed
- `npm run build` in `scratch/clawd-code/sb-ui` — pass
- `python3 -m compileall src/second_brain src/memdir src/agent src/services` — pass
- Browser visual QA on `http://127.0.0.1:8765`: Memory Browser renders, actions are visible, Inspect opens `Memory Detail`, provenance and events render without horizontal overflow in the modal.

### Remaining Architecture Gap
- Auto Dream currently reads the most recent episodic memories via search limit; it still needs a cursor/windowing policy so old but important clusters are not missed.
- There is no memory conflict-resolution UI yet. When two durable facts disagree, Second Brain still lacks a user-facing review queue.
- Project goal extraction exists at the memory layer, but the Project UI does not yet show AI-proposed goals/reflections as an explicit approval workflow.

---

## 2026-05-13 — Context Budget + Compact Skill

### Research Used
- OpenHands context condenser keeps important initial/recent context and summarizes older history to reduce cost and latency while preserving continuity.
- PicoClaw uses two-tier compaction: synchronous leaf summaries, background higher-level summaries, protected fresh tail, hard-budget recovery, and persistent searchable summary/message storage.
- OpenHarness lists auto-compaction as a core context/memory feature and explicitly preserves task state/channel logs across compression.

### Changes Implemented
- Added `src/services/compact/context_budget.py` with a reusable context budget estimator:
  - model context window lookup
  - reserved output budget
  - low/medium/high/critical pressure states
  - memory budget allocation
  - `should_microcompact`, `should_compact`, and hard-overflow flags
- Reworked `SecondBrainSession._build_memory_block()` so memory injection is budgeted and no longer appends duplicate `refresh_context`, session memory, and `MEMORY.md` blocks.
- Project-scoped refresh now passes `scope=self._active_project_id`, so project chat retrieval stays scoped before it reaches the model.
- Added auto-context-compaction preflight before agent loop execution when context pressure crosses the high threshold.
- Changed compact service to preserve a fresh tail of recent messages verbatim while summarizing only older messages.
- Fixed microcompact production bug: production messages use `role="assistant"`, while old logic only recognized `type="assistant"`.
- Added default web `/compact` skill under `src/second_brain/default_skills/compact/SKILL.md`.
- Added bundled harness `compact` skill under `src/skills/bundled/compact/SKILL.md`.
- Streaming `memory_load_complete` now includes a `context_budget` payload for future UI display.

### Verification
- `PYTHONPATH=. /opt/anaconda3/bin/pytest tests/test_compact_service.py tests/test_microcompact.py tests/test_second_brain_services.py tests/test_second_brain_web.py -q` — 60 passed
- `PYTHONPATH=. /opt/anaconda3/bin/pytest tests/test_second_brain_memdir.py tests/test_second_brain_services.py tests/test_second_brain_web.py tests/test_compact_service.py tests/test_microcompact.py tests/test_skills_system.py tests/test_command_system.py tests/test_agent_loop.py tests/test_repl.py tests/test_tool_system_tools.py tests/test_providers.py -q` — 208 passed
- `PYTHONPATH=. /opt/anaconda3/bin/pytest -q` — 307 passed
- `npm run build` in `scratch/clawd-code/sb-ui` — pass
- `python3 -m compileall src/services/compact src/compact_service src/context_system src/second_brain src/skills` — pass

### Remaining Architecture Gap
- Compact summaries are still only in conversation state; the next step is persistent searchable compact summary storage with expand/search tools, similar to PicoClaw's `short_grep` / `short_expand`.
- Context budget is emitted to SSE but not yet visualized in the web UI as a token pressure meter.
- Auto-compaction is single-pass; no tier-2 background merge of old summaries yet.

---

## 2026-05-13 — Session 7 Risk Follow-up: Project Create/List Reliability

### Changes Implemented
- Project list refresh now preserves last-known-good data when `/api/projects` fails instead of clearing the sidebar and making projects look deleted.
- Sidebar shows a retryable project sync error, loading skeletons for cold starts, a subtle syncing state for background refresh, and a count pill.
- Large project sets now page in small batches instead of rendering the full list at once; active project stays visible even when it is outside the first page.
- Project search now includes todo text, and noisy count badges cap at `99+`.
- New Project modal now preserves draft state on failure, shows a user-facing error, and offers retry.
- Project creation now sends `color` with the create request instead of doing create-then-update from the UI.
- Visual smoke now seeds extra projects and asserts sidebar count/pagination/row limits across desktop and mobile.

### Verification
- `npm run lint` in `scratch/clawd-code/sb-ui` — pass
- `python -m pytest tests/test_second_brain_web.py -q` — 34 passed, 5 skipped
- `npm run build` in `scratch/clawd-code/sb-ui` — pass
- `PYTHON=python npm run visual:smoke` in `scratch/clawd-code/sb-ui` — pass

### Remaining Architecture Gap
- Project archival/recovery still needs a user-facing control plane before true production use.
- Project list performance should be revisited with a 100+ project fixture and a real browser trace before release candidate.

---

## 2026-05-13 — Session 8: Skills Page Claude Customize Redesign

### Changes Implemented
- Redesigned the Skills surface into a Claude Customize-style control plane with a compact topbar, overview cards, search row, status filter rail, skill list, and detail inspector.
- Added readiness chips on every skill row so review/generated skills immediately show whether they are live, ready to activate, blocked by safety, or waiting for rehearsal.
- Added a detail-panel activation switch, lifecycle checklist, trigger chips, source/provenance metrics, review notes, and sticky action rail.
- Added user-facing error notices for skill sync, import, activate, status change, delete, build, rehearsal, rollback, and feedback failure paths.
- Replaced immediate delete with a custom delete confirmation modal that explains slash-command persistence.
- Hardened rendering for incomplete skill metadata so missing `description` or `triggers` does not crash search/detail.
- Extended visual smoke to assert the new Customize topbar, overview cards, lifecycle checklist, activation switch, readiness chip, and delete confirmation modal.

### Verification
- `npm run lint` in `scratch/clawd-code/sb-ui` — pass
- `npm run build` in `scratch/clawd-code/sb-ui` — pass
- `PYTHON=python npm run visual:smoke` in `scratch/clawd-code/sb-ui` — pass
- `python -m pytest tests/test_second_brain_web.py -q` — 34 passed, 5 skipped
- `git diff --check` for touched Session 8 files — pass
- Visual screenshot QA on `desktop-dark-skills.png`; clipped action row was caught and fixed.

### Remaining Architecture Gap
- Skill Builder still needs a provider-failure fixture and larger generated/review skill dataset before release candidate.
- A 20+ skill fixture should be added later to test scrolling, filtering, and detail performance under real clutter.

---

## 2026-05-13 — Session 9/10: Sidebar, Navigation, Theme, Open Source + Production QA Harness

### Changes Implemented
- Replaced ambiguous theme cycling with an explicit `System / Light / Dark` selector in the sidebar footer and top theme control.
- Added `data-theme-mode` on the document root so visual QA can verify persisted theme state without guessing from color alone.
- Added keyboard hardening for mobile navigation: `Escape` now closes the sidebar overlay.
- Reworked Open Source into a product-facing control plane with readiness metrics, private-first scope, publish contract, required metadata, and search-before-generate agent policy.
- Added `scripts/production-qa.mjs` and `npm run qa:production` as a single release gate for lint, production build, backend contracts, visual smoke, and whitespace diff checks.
- Extended visual smoke to assert theme menu options, Open Source metrics/governance, footer action, and theme dataset state across desktop dark, desktop light, and mobile dark.

### Verification
- `npm run lint` in `scratch/clawd-code/sb-ui` — pass
- `npm run build` in `scratch/clawd-code/sb-ui` — pass
- `python -m pytest tests/test_second_brain_web.py tests/test_second_brain_skills.py tests/test_second_brain_services.py -q` — 61 passed, 5 skipped
- `PYTHON=python npm run visual:smoke` in `scratch/clawd-code/sb-ui` — pass
- `PYTHON=python npm run qa:production` in `scratch/clawd-code/sb-ui` — pass
- Browser QA on `http://127.0.0.1:8877/` confirmed theme menu and Open Source dialog controls render correctly.

### Remaining Architecture Gap
- Open Source still needs the real registry/publish queue backend and reuse-search integration before it is more than a control-plane preview.
- Production QA should next add accessibility checks, provider-failure fixtures, and larger data fixtures before release candidate.

---

## 2026-05-13 — Session 6 Production Readiness Loops Before Security Hardening

### Changes Implemented
- Created `production-readiness-audit.md` to track Session 1-10 risks before entering `Session 7 — Security + Local Production Hardening`.
- Hardened Settings secrets:
  - API-key input no longer uses redacted secrets as placeholder text.
  - API-key save is disabled until a replacement key is typed.
  - Backend ignores blank secret updates, preventing accidental provider-key deletion.
  - Settings operations now display inline error notices.
  - `settings.json` writes use temp-file replace.
- Added production static QA:
  - blocks `confirm`, `alert`, `debugger`, `dangerouslySetInnerHTML`, secret placeholders, and literal API-key patterns in UI source,
  - enforces gzip bundle budgets against built assets,
  - runs inside `npm run qa:production`.
- Expanded visual smoke:
  - 37 project fixture,
  - 25 skill fixture,
  - Open Source dialog role/aria assertions,
  - Context Ledger viewport containment assertions.
- Fixed a real visual regression caught by screenshot review:
  - Context Ledger cards overflowed inside the right Memory/Context rail because Radix ScrollArea's inner wrapper expanded to max-content.
  - Constrained the Memory Rail scroll viewport child to `display:block;width:100%;min-width:0`.

### Verification
- `python -m pytest tests/test_second_brain_web.py -q` — 34 passed, 7 skipped
- `npm run lint` in `scratch/clawd-code/sb-ui` — pass
- `node scripts/production-static-check.mjs` in `scratch/clawd-code/sb-ui` — pass
- `npm run build && PYTHON=python npm run visual:smoke` in `scratch/clawd-code/sb-ui` — pass
- `PYTHON=python npm run qa:production` in `scratch/clawd-code/sb-ui` — pass:
  - frontend lint passed,
  - production build passed,
  - static checks passed,
  - backend web/skill/service contracts: 61 passed, 7 skipped,
  - desktop/mobile visual smoke passed,
  - whitespace diff check passed.

### Remaining Architecture Gap
- Next session must be `Session 7 — Security + Local Production Hardening`.
- Open Source still needs a real registry, publish queue, and reuse-search backend.
- Security hardening must add local auth/boundary policy, stronger secret scanning, dependency audit, and CI wiring.
- Session 8 should still debloat large frontend files after security hardening, especially `App.tsx`, `SkillBrowser.tsx`, `ProjectView.tsx`, `ChatCanvas.tsx`, and `index.css`.

---

## 2026-05-13 — Session 7: Security + Local Production Hardening

### Changes Implemented
- Added a shared web security policy in `src/second_brain/web_api.py`:
  - loopback-only Host and client validation,
  - bad/missing Host rejection,
  - origin allowlist for local browser origins,
  - `POST/PUT/DELETE` trusted request header requirement,
  - JSON-only body gate for mutations,
  - 1 MB request body limit,
  - reusable security response headers.
- Hardened both server entrypoints:
  - `web_server.py` now applies the shared policy to JSON, SSE, static, and error responses.
  - `fastapi_app.py` now uses the same policy and headers through middleware.
- Refused unsafe remote binding unless `SECOND_BRAIN_ALLOW_REMOTE_BIND=1` is explicitly set.
- Updated frontend API calls and visual smoke seed fixtures to send `X-Second-Brain-Request: 1`.
- Expanded `production-static-check.mjs` to scan backend source plus `pyproject.toml` and `requirements.txt` for security regressions.
- Ran `pip-audit`; found `pyjwt 2.8.0` via `zhipuai` with `CVE-2026-32597`.
- Removed `zhipuai` from core dependencies and switched `GLMProvider` to the OpenAI-compatible endpoint so GLM support does not carry the vulnerable transitive dependency.
- Added regression tests for Host/DNS rebinding, remote bind policy, trusted mutation header, content-type/body limit, FastAPI gateway security, and GLM provider client construction.
- Created `security-hardening-audit.md` as the Session 7 source of truth.

### Verification
- `python -m pytest tests/test_second_brain_web.py -q` — 39 passed, 8 skipped
- `PYTHONPATH=/tmp/second-brain-fastapi-test:$PWD python -m pytest tests/test_second_brain_web.py -q` — 47 passed, 2 warnings
- `python -m pytest tests/test_second_brain_web.py tests/test_second_brain_skills.py tests/test_second_brain_services.py tests/test_providers.py -q` — 95 passed, 8 skipped
- `npm run lint` in `scratch/clawd-code/sb-ui` — pass
- `node scripts/production-static-check.mjs` in `scratch/clawd-code/sb-ui` — pass, 40 source/manifest files scanned
- `npm audit --omit=dev --audit-level=high --json` — 0 vulnerabilities
- `PYTHONPATH=/tmp/second-brain-pip-audit python -m pip_audit -r requirements.txt` — no known vulnerabilities found
- `PYTHON=python npm run qa:production` in `scratch/clawd-code/sb-ui` — pass

### Remaining Architecture Gap
- Current security boundary is desktop-local hardening, not user authentication.
- Python dependency audit is verified manually through temp `pip-audit`; Session 9 should make it CI-owned.
- Dependency manifests still use broad lower-bound specs; Session 8/9 should move toward lockfile/reproducible install.
- Open Source still needs registry, publish queue, reuse search, and permission model.
- A packaged desktop wrapper still needs sandbox/update/protocol hardening before release candidate.

---

## 2026-05-13 — Session 8: Debloat + File Architecture Cleanup

### Changes Implemented
- Reduced `sb-ui/src/App.tsx` from 1,598 lines to 959 lines by extracting modal surfaces, chat helpers, event/activity helpers, and theme helpers.
- Reduced `sb-ui/src/components/SkillBrowser.tsx` from 1,195 lines to 696 lines by moving lifecycle helpers and modal bodies into dedicated files.
- Split `sb-ui/src/index.css` from 7,150 lines into 10 scoped style modules while preserving cascade order through imports.
- Extracted backend web security policy from `web_api.py` into `web_security.py`, reducing `web_api.py` to 508 lines.
- Added architecture line budgets to `production-static-check.mjs` so file bloat fails production QA.
- Created `debloat-architecture-audit.md` as the Session 8 source of truth.

### Verification
- `npm run build` in `scratch/clawd-code/sb-ui` — pass
- `npm run lint` in `scratch/clawd-code/sb-ui` — pass
- `node scripts/production-static-check.mjs` in `scratch/clawd-code/sb-ui` — pass
- `python -m pytest tests/test_second_brain_web.py -q` — 39 passed, 8 skipped
- `PYTHONPATH=/tmp/second-brain-fastapi-test:$PWD python -m pytest tests/test_second_brain_web.py -q` — 47 passed, 2 warnings
- `python -m pytest tests/test_second_brain_web.py tests/test_second_brain_skills.py tests/test_second_brain_services.py tests/test_providers.py -q` — 95 passed, 8 skipped
- `PYTHON=python npm run qa:production` in `scratch/clawd-code/sb-ui` — pass
- `git diff --check` for touched Session 8 files — pass
- Visual smoke screenshots generated: 24

### Remaining Architecture Gap
- `session.py`, `web_runtime.py`, `api.ts`, `ProjectView.tsx`, and `ChatCanvas.tsx` remain too large for the final production bar.
- CSS is now scoped, but `project.css` and `skills.css` should be split again after component decomposition.
- Session 9 must make the production test matrix and dependency audits CI-owned instead of manual discipline.

---

## 2026-05-13 — Session 8 Follow-up Loop: Frontend Domain Split + Budget Ratchet

### Changes Implemented
- Split `sb-ui/src/lib/api.ts` from 1,087 lines into an 8-line facade plus domain clients under `sb-ui/src/lib/api/`.
- Split `ChatCanvas.tsx` from 969 lines to 248 lines by extracting:
  - `ChatActivityPanel.tsx`
  - `ChatEmptyState.tsx`
  - `ChatMarkdown.tsx`
  - `ChatMessageBubble.tsx`
  - `ChatProgressRail.tsx`
  - `ChatStatusLine.tsx`
- Split `project.css` into `project-sidebar-chat.css`, `project-workspace.css`, and `project-command-surface.css`.
- Split `skills.css` into `skills-control-plane.css` and `skills-modals.css`.
- Extracted Project view modals/support into `ProjectViewSupport.tsx`, reducing `ProjectView.tsx` to 813 lines.
- Ratcheted `production-static-check.mjs` line budgets downward for API clients, Chat components, Project support, and CSS modules.

### Verification
- `npm run lint` in `scratch/clawd-code/sb-ui` — pass
- `npm run build` in `scratch/clawd-code/sb-ui` — pass
- `node scripts/production-static-check.mjs` in `scratch/clawd-code/sb-ui` — pass, 81 source files scanned
- `python -m pytest tests/test_second_brain_web.py tests/test_second_brain_skills.py tests/test_second_brain_services.py tests/test_providers.py -q` — 95 passed, 8 skipped
- `PYTHON=python npm run qa:production` in `scratch/clawd-code/sb-ui` — pass in 73.0s
- `git diff --check` for touched Session 8 files — pass
- Visual smoke screenshots generated: 24

### Remaining Architecture Gap
- `session.py` and `web_runtime.py` remain the largest backend debt and need behavior-aware splitting after Session 9 gates are in place.
- `App.tsx`, `ProjectView.tsx`, and `MemoryBrowser.tsx` are still large, but the immediate merge-collision risk is lower after API/chat/CSS decomposition.
- Next session must be `Session 9 — Production Test Matrix + CI Gate`.

---

## 2026-05-14 — Session 9: Production Test Matrix + CI Gate

### Changes Implemented
- Added `npm run qa:production` as the single local/CI release gate for Second Brain Web Surface.
- Added GitHub Actions workflow at `.github/workflows/second-brain-production.yml`.
- Added `scripts/python-dependency-audit.py` for cached `pip-audit` checks against `requirements.txt`.
- Added `scripts/run-fastapi-contracts.py` so FastAPI TestClient web tests run for real and fail if skipped.
- Extended production QA to include frontend lint/build, npm audit, Python audit, static/bundle/line-budget checks, FastAPI contracts, backend skill/service/provider contracts, visual smoke, and whitespace diff check.
- Made skipped production checks fail the gate so audit/visual coverage cannot become a false-green release.
- Added `PRODUCTION_QA.md` and `production-test-matrix.md` as the source of truth for the release gate.
- Hardened `visual-smoke.mjs` for CI Chrome discovery and project-chat render timing.

### Verification
- `python scripts/python-dependency-audit.py` — pass, no known vulnerabilities
- `python scripts/run-fastapi-contracts.py` — pass, 47 passed, 2 `httpx` deprecation warnings
- `node --check scripts/production-qa.mjs && node --check scripts/visual-smoke.mjs` — pass
- `node scripts/production-static-check.mjs` — pass, 81 source files scanned
- `npm run visual:smoke` in `scratch/clawd-code/sb-ui` — pass, 24 screenshots
- `PYTHON=python npm run qa:production` in `scratch/clawd-code/sb-ui` — pass in 55.6s, 9/9 checks

### Remaining Production Gap
- Python dependencies still need a reproducible lock policy beyond broad `requirements.txt` ranges.
- FastAPI contract tests still emit `httpx` deprecation warnings; this must be cleaned before release candidate.
- Visual smoke is comprehensive but slow; keep it as release gate unless a faster PR gate is added without reducing coverage.
- Security is hardened for local desktop use, not authenticated commercial deployment.
- Session 10 should use this gate before every product-polish batch.
