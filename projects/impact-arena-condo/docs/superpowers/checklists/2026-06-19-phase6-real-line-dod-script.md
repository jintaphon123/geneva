# Phase 6 Real LINE Definition Of Done

Date: 2026-06-19
Status: OPEN

## Fixture Boundary

- [x] Use one booking, room, Cleaning Task, Access Prep Task, Internal admin, and Housekeeping operator marked with `PHASE6_REAL_LINE_DOD`.
- [x] Do not reuse a production guest booking.
- [x] Mask LINE identities in evidence.
- [x] Record task IDs, source event IDs, incident IDs, notification/outbox IDs, and readiness results.
- [ ] Clean fixture rows only after database evidence is captured.

## Button Script

- [ ] Housekeeping taps `งานวันนี้`.
- [ ] Housekeeping taps `คิวงาน`.
- [ ] Five task cards render and page navigation works.
- [ ] Housekeeping taps `รับงาน` / the current accept label.
- [ ] The selected task is assigned and acknowledged once.
- [ ] Housekeeping taps `เริ่มทำ`.
- [ ] Housekeeping taps `แจ้งปัญหา`.
- [ ] Housekeeping taps `ไม่ได้ใส่น้ำ`.
- [ ] Internal Ops receives the problem alert.
- [ ] Owner notification evidence exists.
- [ ] Housekeeping taps `เสร็จแล้ว`.
- [ ] Completion is blocked while water is missing.
- [ ] Water is restored.
- [ ] Cleaning Task completes.
- [ ] Access Prep remains open and separate.
- [ ] An unauthorized operator attempts Access Prep and is rejected.
- [ ] Authorized operator/Admin completes Access Prep.
- [ ] Internal Ops shows Cleaning Ready and Access Prep Ready separately.
- [ ] Guest OA room-entry remains blocked before Access Prep completion.
- [ ] Guest OA room-entry becomes eligible only after Access Prep completion.
- [ ] Replaying one postback creates no duplicate transition or incident.

## Database Evidence

- [x] Cleaning lifecycle events are ordered and idempotent.
- [x] Checklist records show water missing, restored, then complete.
- [x] Access Prep lifecycle and `key_custody` are correct.
- [x] `housekeeper_task_focus` points only to the current assigned task.
- [x] Direct reassignment invalidates the previous operator focus.
- [x] Problem incident has both Internal Ops and owner logical recipients.
- [x] No unauthorized Access Prep mutation occurred.
- [x] `get_room_access_readiness` blockers are correct before and after.
- [x] Outbound evidence never claims delivery without provider evidence.

## Verdict

Phase 6 closes only when every checkbox above has real LINE and database evidence. Synthetic or direct-RPC evidence cannot replace the button-tap pass.

Current blockers:
- Real LINE button-tap execution is partially complete, pending remaining steps.
