# Impact Arena Condo — Project Intelligence Log

Log สะสมผลลัพธ์จากทุก skill ที่รันในโปรเจคนี้
เรียงจากใหม่สุด → เก่าสุด

---

## 2026-05-03 — THAIFEX Outreach Plan

**งานที่ทำ:** ออกแบบ AI-powered outreach pipeline สำหรับ THAIFEX 26-30 พ.ค.

**Key findings:**
- Exhibitor list ต้องล็อกอิน — Bond register เป็น Visitor ที่ registration.thaifex-anuga.com (ฟรี)
- 10times.com / thaifex-anuga.com ปิด public API → ต้องดึงข้อมูลเองก่อน
- Facebook Page message = channel ที่ดีที่สุดสำหรับ SME ไทย
- 5-phase pipeline: List → Research → Messages → Send → Track

**Next action สำหรับ Bond:**
Register Visitor → ดึง list 50-100 บริษัท SME ไทย → บันทึกใน `scratch/thaifex-raw.md` → แจ้ง Claude ใน session หน้าว่า "เริ่ม THAIFEX outreach"

**Output files:**
- `projects/impact-arena-condo/thaifex-outreach-plan.md` — แผนเต็ม + template + timeline

---

## 2026-05-03 — /consult

**คำถาม:** กลยุทธ์หาลูกค้าและเพิ่มรายได้ห้องพักรายวัน Impact Arena Condo

**Key Findings:**
- Booking.com ranking factor #1 ปี 2026 = response time, ตามด้วย recent reviews (3 เดือนล่าสุด weighted สูงสุด), 24+ photos, conversion rate, calendar availability — ทุกอย่างแก้ได้ฟรี
- คะแนน 8–9 บน Booking ให้ conversion สูงขึ้น 15–20% ทันที (Booking 2025 update) — C5 อยู่ที่ 8.0 ใกล้จุดเปลี่ยนแล้ว
- ปัญหาจริงของ Bond = ไม่มี direct channel/database ของตัวเอง ทุกจองขึ้นอยู่กับ algorithm; แม่ชนะเพราะมี Line relationship สะสมกับ exhibitors/booth staff
- กลุ่ม Staff/ผู้เปิดบูธงาน (THAIFEX, Motor Expo ฯลฯ) = ลูกค้าทองคำ พัก 5–14 วัน แต่ Bond เข้าไม่ถึงผ่าน Booking — ต้อง direct outreach
- Review score ceiling สำหรับ C3/C4/C9 = ~7.8 เพราะปัญหา physical (แมลงสาบ, ความสะอาด) — ไม่สามารถดันเกินด้วย OTA tactics อย่างเดียว

**Recommendations ที่ให้ (เรียงตาม priority):**
1. **Action #1 — ปรับ C5 listing ภายใน 7 วัน:** ตอบ message < 1 ชั่วโมง, เพิ่มรูป 24+, ขอ review ทันทีหลัง checkout, เปิด calendar 6 เดือน → คาดว่าคะแนน 8.0 → 8.3–8.5 ใน 30 วัน (Confidence: สูง)
2. **Action #2 — สร้าง Line OA + Lead Magnet:** ติดป้าย A4 ในห้อง "แอด Line รับ Late Checkout ฟรี" → convert Booking guests เป็น direct contacts → ลด dependency จาก platform ทีละคน (Confidence: สูง)
3. **Action #3 — Cold outreach exhibitors ก่อน THAIFEX 26 พ.ค.:** ใช้ exhibitor directory ทักผ่าน Facebook/Line 10–20 บริษัท/วัน เฉพาะ 2 สัปดาห์ก่อนงาน → ต้อง exclude regular clients ของแม่ก่อนเสมอ (Confidence: ปานกลาง)

**สิ่งที่ยังไม่ควรทำ (พร้อมเหตุผล):**
- Social media / Content creator เมืองทอง → ใช้เวลา 3–6 เดือนกว่าเห็นผล ไม่ใช่ Phase 1
- Tour operators → margin ต่ำ, cycle ยาว
- Agoda/Airbnb optimization → fix Booking ก่อน

**Risks ที่ระบุ:**
- ถ้า ranking ไม่ขึ้นใน 30 วัน → ตรวจ cancellation rate ก่อน
- ถ้า C5 ยังมีปัญหา pest → ใช้เงิน 500–1,500 บาททำ pest control ก่อน (use case เดียวที่ควรใช้เงิน 2,000 บาท)
- Exhibitor outreach ต้อง coordinate กับแม่ก่อนเสมอ

**Output ที่สร้าง:**
- `scratch/impact-arena-strategy.docx` — เอกสาร Word ฉบับสมบูรณ์พร้อม tables, events calendar, template messages

**Events สำคัญที่ track ไว้:**
- THAIFEX: 26–30 พ.ค. 2569 (23 วันจากนี้ — urgent)
- Motor Expo: 2–13 ธ.ค. 2569 (เริ่ม outreach ต.ค.)

---
