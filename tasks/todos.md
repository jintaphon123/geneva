# MyBrain — Master Todo List

อัปเดตล่าสุด: 2026-05-04
ทุก session ที่มีงานใหม่เกิดขึ้น → append ที่นี่ทันที

Legend: 🔥 Urgent (< 7 วัน) | ⭐ Important | 🟡 Normal | ✅ Done | ❌ Dropped

---

## 🏠 Impact Arena Condo

### Ongoing (ทำทุกครั้ง)
- [ ] ⭐ ส่ง review request message หลัง guest checkout ทุกครั้ง → ใช้ template ใน log.md
- [ ] ⭐ ตอบ Booking.com message ทุก inquiry ภายใน 1 ชั่วโมง

### This Week
- [ ] 🔥 คุยกับแม่เรื่อง regular exhibitor clients → ขอรายชื่อที่ต้อง exclude ก่อน outreach
- [ ] 🔥 พิมพ์ QR Code Line OA ติดห้อง C5 ทุกห้อง (แลกรับ Late Checkout ฟรี)

### THAIFEX 26–30 พ.ค. (23 วัน) — ดู thaifex-outreach-plan.md
- [ ] 🔥 **[Phase 1]** Register เป็น Visitor ที่ registration.thaifex-anuga.com → ดึง list SME ไทย 50-100 บริษัท → บันทึกใน `scratch/thaifex-raw.md`
- [ ] 🔥 **[Phase 2]** แจ้ง Claude "เริ่ม THAIFEX outreach" → Claude รัน WebSearch หา Facebook URL + score priority
- [ ] 🔥 **[Phase 3]** Claude generate personalized messages ทุกบริษัท → บันทึกใน `scratch/thaifex-messages.md`
- [ ] 🔥 **[Phase 4]** Bond ส่ง 10 messages/วัน ผ่าน Facebook Page (paste จาก messages file)
- [ ] ⭐ **[Phase 5]** Claude track responses + generate follow-up messages

### LOVE OUT LOUD FAN FEST 22–24 พ.ค. (19 วัน)
- [ ] 🔥 หา Facebook fan group ของ artist ที่มา LOVE OUT LOUD → โพสต์ขอที่พัก
- [ ] 🔥 Template: "ใครจะมาดู [artist] แล้วยังไม่มีที่พัก? คอนโด 5 นาทีจาก Impact Arena ราคา [xxx] บาท ติดต่อ [Line]"

### Laufey Concert 31 พ.ค.
- [ ] ⭐ หา Laufey Thailand fan group → โพสต์ก่อนงาน 1 สัปดาห์ (โพสต์วันที่ ~24 พ.ค.)

### ใหม่ เจริญปุระ MTERTAINMENT 20 มิ.ย.
- [ ] ⭐ โพสต์ใน fan group / Facebook Event ก่อนงาน 1 สัปดาห์ (~13 มิ.ย.)

### Motor Expo 2–13 ธ.ค.
- [ ] 🟡 เริ่ม exhibitor outreach ตั้งแต่ ต.ค. (set reminder ไว้แล้วใน Calendar)

### Long-term
- [ ] 🟡 Deep clean + pest control ห้อง C3/C4/C9 (เมื่อมีเงิน ~500-1,500 บาท)
- [ ] 🟡 Renovate ห้อง → ขยับ tier ราคาขึ้น (เมื่อมีรายได้สม่ำเสมอ)
- [ ] 🟡 จ้างแม่บ้าน (เมื่อ occupancy > 15 ห้อง/คืน)
- [ ] 🟡 Line OA bot จัดคิวแม่บ้าน

---

## 🧠 Second Brain / Senior Project

### Month 1 — พ.ค. 2026 (Build + Dog-food)
- [ ] 🔥 **[Week 1-2]** Build MVP v0: auto-capture + cross-session memory + AI-to-AI handoff prototype (online, ไม่ใช่ local)
- [ ] 🔥 **[Week 3]** Bond ใช้กับ KU coursework จริง → บันทึก what works/doesn't
- [ ] 🔥 **[Week 4]** Demo กับ 3-5 KU Senior Project teams — วัดว่ามีใครขอ access เองไหม

### Agent Harness Build Order (จาก deep research 2026-05-08)
- [ ] 🔥 **[Step 1]** Memory-as-files layer: lexical retrieval จาก markdown + session autosave + memory update pipeline หลัง session จบ → ใช้ `score_memory()` pattern จาก research
- [ ] 🔥 **[Step 2]** Tool runner + HookBus + hard budgets: `PreToolUse` block, `PostToolUse` audit log, `session.end` transcript save, max turns/cost guard — hook bus ต้อง built ก่อน feature ใหญ่ทุกอย่าง
- [ ] ⭐ **[Step 3]** Skill loader: scan `.claude/skills/`, inject summaries เท่านั้น ใน system prompt, expand full body เฉพาะตอน invoke — discover → select → expand → execute
- [ ] ⭐ **[Step 4]** Claude proposer → Gemini challenger pattern (เฉพาะหลัง step 1-2 stable + มี eval traces แล้ว)
- [ ] ⭐ อ่าน Pydantic AI harness source: github.com/pydantic/pydantic-ai-harness (primary reference)
- [ ] ⭐ อ่าน OpenHands context condenser + stuck detector pattern (secondary reference)

### Month 2 — มิ.ย. 2026 (Validate + Recruit)
- [ ] ⭐ ให้ 3-5 KU project teams (15-30 users) ทดลองจริง 14 วัน → วัด retention (≥60% = GO signal)
- [ ] ⭐ สังเกต: ทีมไหนใช้ AI handoff แทนการ brief กัน? → นั่นคือ proof of value
- [ ] ⭐ Pitch co-founders 2-3 คน ด้วย real usage data ไม่ใช่ slides

### Month 3 — ก.ค. 2026 (Lock + Submit)
- [ ] ⭐ Form KU team + ร่าง Senior Project proposal ร่วมกัน
- [ ] ⭐ Submit Senior Project proposal to KU advisor
- [ ] ⭐ Apply NIA grant (ต้องหา deadline ก่อน ← ทำสัปดาห์นี้)

### Immediate Actions (ทำสัปดาห์นี้)
- [ ] 🔥 หา NIA grant deadline รอบปัจจุบัน → เว็บ NIA Thailand
- [ ] ⭐ เดินเข้าออฟฟิศ KU admin → ถามว่ามี budget authority ซื้อ software เองได้ไหม
- [ ] ⭐ ยืนยัน Senior Project deadline (ปักหมุดลงใน Calendar ทันทีที่ได้วันแน่)
- [ ] ⭐ ตั้ง daily startup log ใน Second Brain (บันทึกทุกวัน: build อะไร, เจออะไร)

### Co-Founder Pipeline
- [ ] ⭐ Recruit Art + Soda ผ่าน Claude Course dashboard (ongoing)
- [ ] 🟡 เตรียม pitch narrative สำหรับ KU classmates คนอื่น (ใช้ one-liner: "AI ที่จำทุกอย่างที่คุณรู้")
- [ ] 🟡 หา Thai B2G founder สัก 1 คนเพื่อ interview (defer ไปหลัง prototype ready)

### Long-term
- [ ] 🟡 Apply DEPA grant (หลัง Senior Project accepted)
- [ ] 🟡 Check KU Innovation Hub / Startup Space สำหรับ co-working + mentorship

---

## 🎓 Academic (KU 3rd Year ME)

- [ ] 🟡 ใส่วันสอบ Midterm ใน Calendar (ยังไม่มีวันแน่นอน)
- [ ] 🟡 ใส่วันสอบ Final ใน Calendar (ยังไม่มีวันแน่นอน)
- [ ] 🟡 IELTS / TOEIC — เช็ค deadline และ schedule สอบ

---

## ✅ Completed

- [x] 2026-05-03 — สร้าง Line OA "Impact Arena Condo" เรียบร้อยแล้ว (รอเปลี่ยนชื่อ)
- [x] 2026-05-03 — ถ่ายรูปห้องทุกมุมครบแล้ว
- [x] 2026-05-03 — เปิด Calendar ล่วงหน้า 1 ปีแล้ว
- [x] 2026-05-03 — อัปเดต context.md Impact Arena Condo ครบถ้วน
- [x] 2026-05-03 — สร้าง log.md สำหรับ Impact Arena Condo
- [x] 2026-05-03 — สร้าง impact-arena-strategy.docx

---

## 📝 How to use

- เพิ่ม task ใหม่ → append ใต้หมวดที่เกี่ยวข้อง
- เสร็จแล้ว → ย้ายไป ✅ Completed พร้อมวันที่
- ทุก skill run ที่มี action items → Claude เพิ่ม tasks ใหม่ที่นี่อัตโนมัติ
- Deadline items → sync ไปยัง Google Calendar (Work calendar)
