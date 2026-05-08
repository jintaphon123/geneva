# Capability Gaps Log

Ongoing log of gaps Claude has identified in its own skill set, context, or tooling within this system.

| Date | Gap Identified | What Triggered It | Proposed Fix | Status |
|------|---------------|-------------------|--------------|--------|
| 2026-04-25 | ไม่มี skill สำหรับ onboarding file ที่วางผิดที่ (เช่น CLAUDE2.md, SKILL.md, reference.md ที่ root) | Session นี้ต้องอ่านและ analyze ไฟล์ 3 ตัวที่วางผิดที่ด้วยตัวเอง ไม่มี SOP รองรับ | สร้าง SOP `references/sops/file-triage.md` — checklist สำหรับ audit ไฟล์แปลกปลอมที่ root แล้ว route ไปที่ถูกต้อง | ✅ Resolved 2026-04-26 |
