# THAIFEX 2026 — AI-Powered Outreach Plan

งาน: THAIFEX – Anuga Asia | วันที่: 26–30 พ.ค. 2569
เป้าหมาย: จองห้องจาก Staff/ผู้เปิดบูธ SME ไทย ผ่าน direct outreach ก่อนงาน

---

## ทำไมต้องทำแผนนี้

Booking.com ไม่ถึงกลุ่ม exhibitors — พวกเขาจองตรงผ่าน Line/WhatsApp
แม่ Bond ได้กลุ่มนี้เพราะมี relationship สะสมมาหลายปี
Bond ต้องสร้าง pipeline ของตัวเองด้วย cold outreach ก่อนงาน

---

## Pipeline Overview (5 Phases)

```
[Phase 1] Bond ดึง List  →  [Phase 2] AI Research Contacts
          ↓                            ↓
[Phase 5] Track & Follow-up  ←  [Phase 4] Bond ส่ง  ←  [Phase 3] AI Generate Messages
```

---

## Phase 1 — ดึง Exhibitor List (Bond ทำ 1 ครั้ง, ใช้เวลา 15-30 นาที)

**ปัญหา:** Exhibitor list ต้องล็อกอินก่อน ไม่มี public API

**ขั้นตอน:**
1. ไป [registration.thaifex-anuga.com/event/THAA26](https://registration.thaifex-anuga.com/event/THAA26)
2. Register เป็น **Visitor** (ฟรี) ด้วยอีเมล Bond
3. เมื่อเข้าไปได้แล้ว → หน้า Exhibitor Search/Directory
4. Filter: **Country = Thailand**, **Category = Food/Beverage Manufacturer**
5. Export หรือ copy บริษัท 50-100 ราย → วาง paste ลงใน `scratch/thaifex-raw.md`

**ทางเลือก (ถ้า Register ยุ่งยาก):**
- เปิด Chrome → ไป 10times.com/thaifex-worldfood-asia/exhibitors → Scroll จนสุด → copy ชื่อบริษัทลงไฟล์
- ไม่ต้องครบทุกบริษัท — เอาแค่ 50 รายแรกที่ดูเหมือน SME ไทยก็พอ

**Output ที่ต้องการ:**
```
# THAIFEX Raw List
- บริษัท ก ฟู้ดส์ จำกัด
- บริษัท ข เบเวอเรจ จำกัด
- ห้างหุ้นส่วนจำกัด ค อาหาร
...
```
บันทึกลง `scratch/thaifex-raw.md`

---

## Phase 2 — AI Research: หา Facebook + Contact (Claude ทำอัตโนมัติ)

**เมื่อ Bond วาง list ลง scratch/thaifex-raw.md แล้ว บอก Claude:**
> "รัน THAIFEX research phase"

**Claude จะทำ:**
สำหรับแต่ละบริษัทใน list:
1. `WebSearch("[ชื่อบริษัท] Facebook Thailand")` → หา Facebook Page URL
2. `WebSearch("[ชื่อบริษัท] contact email website")` → หา email/website
3. Score priority (ดูหัวข้อ Scoring Criteria ด้านล่าง)
4. บันทึกผลลง `scratch/thaifex-researched.md`

**Output format:**
```markdown
| # | บริษัท | Facebook URL | Website | Email | Score | หมายเหตุ |
|---|--------|-------------|---------|-------|-------|---------|
| 1 | ก ฟู้ดส์ | fb.com/... | gfoods.co.th | - | 🔥 High | SME ภาคกลาง |
| 2 | ข เบเวอเรจ | - | - | info@kh.com | 🟡 Med | ไม่เจอ FB |
```

**Scoring Criteria (AI ใช้ตัดสิน):**
- 🔥 **High** (Contact ก่อน): SME ไทย + อยู่ต่างจังหวัด + มี FB Page + ไม่ใช่ franchise ใหญ่
- ⭐ **Medium**: บริษัทไทย แต่อาจมีโรงแรมประจำอยู่แล้ว หรือ Bangkok-based
- 🟡 **Low**: International company / ยักษ์ใหญ่ / ไม่เจอ contact ใดเลย

---

## Phase 3 — AI Generate Messages (Claude เขียนให้ทุกบริษัท)

**เมื่อ research เสร็จแล้ว บอก Claude:**
> "Generate THAIFEX outreach messages จาก scratch/thaifex-researched.md"

**Claude จะสร้าง message แบบ personalized สำหรับแต่ละบริษัท:**

### Template Base (Claude ปรับตามข้อมูลบริษัท):
```
สวัสดีครับ [ชื่อบริษัท/แอดมิน]

ทราบว่าทางบริษัทจะมาออกบูธงาน THAIFEX Anuga Asia 
วันที่ 26-30 พ.ค. นี้ที่ Impact Arena ครับ

ผมมีห้องพักคอนโดอยู่ใกล้กับ Impact Arena มาก (เดินแค่ 5 นาที) 
ราคาคืนละ [xxx] บาท สะดวกสบาย มีที่จอดรถ

ถ้าทีมงานยังไม่มีที่พักช่วงงาน จองตรงกับผมผ่าน Line 
ราคาถูกกว่า Booking.com 15-20% ครับ

สนใจหรือต้องการข้อมูลเพิ่มเติมแจ้งได้เลยนะครับ 🙏
[Line ID / เบอร์โทร]
```

**Variations ที่ Claude จะ generate (A/B test):**

| Version | จุดเน้น | ใช้กับ |
|---------|--------|-------|
| A — Proximity | "เดิน 5 นาทีถึง hall" | บริษัทที่ต้องขนของมาก |
| B — Price | "ถูกกว่า Booking 20%" | SME งบจำกัด |
| C — Team | "รับได้ทีละ 3-5 ห้องในราคาพิเศษ" | บริษัทที่มาหลายคน |
| D — Urgency | "ห้องใกล้งานเหลือน้อยแล้วครับ" | ส่ง 3 วันก่อนงาน |

**Output:** `scratch/thaifex-messages.md` — รายชื่อบริษัท + message พร้อมส่ง

---

## Phase 4 — Bond ส่ง (Manual แต่ AI ช่วย Queue)

**ทำไมต้องส่งเอง:**
Facebook/Line ห้าม bot ส่ง message จะโดน ban account ทันที
แต่ Bond ใช้เวลาแค่ 3-5 นาที/บริษัท ถ้า message พร้อมแล้ว

**Flow ที่ Bond ทำ:**
1. เปิด `scratch/thaifex-messages.md`
2. เปิด Facebook บนมือถือ
3. ค้นหา Facebook Page ของบริษัท (link อยู่ใน researched list แล้ว)
4. กด "ส่งข้อความ" → paste message จากไฟล์ → ส่ง
5. mark ว่า "Sent" ในไฟล์ tracking

**Daily quota:** 10 บริษัท/วัน × 14 วัน = 140 messages ก่อนงาน

---

## Phase 5 — Tracking & Follow-up (AI จัดการ)

**Tracking file:** `scratch/thaifex-tracking.md`

```markdown
| บริษัท | Facebook URL | ส่งวันที่ | Status | หมายเหตุ |
|--------|-------------|----------|--------|---------|
| ก ฟู้ดส์ | fb.com/... | 5 พ.ค. | ✅ Sent | |
| ข เบเวอเรจ | fb.com/... | 5 พ.ค. | 💬 Replied | สนใจ 3 คืน |
| ค อาหาร | fb.com/... | 5 พ.ค. | ❌ No FB | ลอง email |
```

**Follow-up ที่ Claude จะ generate:**
- วันที่ 3 หลังส่ง: ถ้าไม่ตอบ → ส่ง follow-up (shorter, different angle)
- "สวัสดีครับ ขอถามอีกครั้งเรื่องที่พักช่วง THAIFEX ครับ มีห้องว่างอยู่ครับ"

---

## Phase 6 — Capture & Retain (หลังงาน)

สำหรับทุก exhibitor ที่ตอบกลับ หรือมาพักจริง:
- ขอแอด Line OA ทันที
- Tag ว่า "THAIFEX 2026"
- ก่อน THAIFEX 2027 (ม.ค.-ก.พ.) → broadcast ล่วงหน้าก่อนใคร

---

## Timeline

| วันที่ | Action |
|--------|--------|
| **3-5 พ.ค.** (ตอนนี้) | Bond ดึง exhibitor list → บันทึกใน scratch/ |
| **5-6 พ.ค.** | Claude รัน Phase 2 (research contacts) |
| **6-7 พ.ค.** | Claude รัน Phase 3 (generate messages) |
| **7-20 พ.ค.** | Bond ส่ง 10 messages/วัน |
| **10-22 พ.ค.** | Claude track + generate follow-ups |
| **26-30 พ.ค.** | งาน THAIFEX — ห้องควรเต็มบางส่วน |
| **หลังงาน** | เก็บ contacts → prep for Motor Expo |

---

## How to Start Next Session

พิมพ์ใน Chat:
> "เริ่ม THAIFEX outreach — ฉันได้ list มาแล้ว บันทึกไว้ที่ scratch/thaifex-raw.md"

Claude จะรัน Phase 2 → Phase 3 ต่อทันที

---

## Notes

- **อย่า include** บริษัทในรายชื่อ regular clients ของแม่ (ต้องถามแม่ก่อน)
- Facebook Page message: response rate ดีกว่า email สำหรับ SME ไทย
- ถ้าบริษัทไม่มี Facebook → ลอง email จาก website เป็น fallback
- ถ้า THAIFEX ได้ผลดี → ใช้ exact same pipeline กับ Motor Expo ธ.ค. (เริ่ม ต.ค.)
