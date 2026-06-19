export type Platform = 'booking' | 'agoda' | 'airbnb' | 'line' | 'direct' | 'other'
export type BookingStatus = 'draft' | 'confirmed' | 'checked_in' | 'checked_out' | 'cancelled' | 'no_show'
export type Portfolio = 'bond' | 'mom'
export type CleaningStatus = 'clean' | 'dirty' | 'cleaning_in_progress' | 'unknown'
export type OccupancyStatus = 'occupied' | 'vacant' | 'checking_in' | 'checking_out' | 'unknown'

export interface Room {
  id: string
  room_code: string
  building: string
  floor: number
  room_number: string
  portfolio: Portfolio
  listing_tier: string
  quality_tier: number
  active: boolean
  photo_url?: string | null
}

export interface RoomStatus {
  room_id: string
  cleaning_status: CleaningStatus
  occupancy_status: OccupancyStatus
  maintenance_status: 'ok' | 'needs_attention' | 'blocked'
  last_cleaned_at: string | null
  updated_at: string
}

export interface Booking {
  id: string
  platform: Platform
  reservation_number: string | null
  guest_name_snapshot: string
  check_in_date: string
  check_out_date: string
  nights: number
  room_id: string | null
  booking_status: BookingStatus
  booking_status_updated_at: string | null
  created_at: string
  updated_at: string
  // joined fields
  room_code: string | null
  building: string | null
  portfolio: Portfolio | null
  cleaning_status: CleaningStatus | null
  occupancy_status: OccupancyStatus | null
  photo_url?: string | null
}

export interface Alert {
  id: string
  case_code: string | null
  case_type: string
  priority: 'low' | 'normal' | 'high' | 'urgent'
  status: string
  room_code_snapshot: string | null
  guest_display_snapshot: string | null
  reservation_number_snapshot: string | null
  issue_summary: string | null
  ai_suggestion: string | null
  admin_action_needed: string | null
  booking_id: string | null
  created_at: string
  // D2 case-detail fields — optional: selected with progressive fallback, may be absent in some envs
  platform_snapshot?: string | null
  channel_target?: string | null
  check_in_date_snapshot?: string | null
  check_out_date_snapshot?: string | null
  latest_guest_message_excerpt?: string | null
  active_message_draft_id?: string | null
  assigned_admin_user_id?: string | null
}

// Active hold that blocks Room Access Package delivery until the booking is safe.
export interface RoomAccessHold {
  id: string
  booking_id: string | null
  room_id: string | null
  hold_type: string | null
  hold_reason: string | null
  hold_status: string | null
  priority: string | null
  created_at: string | null
  released_at?: string | null
  last_recheck_result?: string | null
}

// Stay-specific runtime signals — used for evidence language on Today
// (e.g. "ยังไม่มีสัญญาณ check-in" instead of falsely claiming the guest hasn't arrived).
export interface GuestStayState {
  booking_id: string | null
  check_in_signal_status: string | null
  check_out_signal_status: string | null
  room_access_package_status: string | null
  booking_verification_status: string | null
  journey_stage: string | null
  updated_at: string | null
}

export interface MessageDraft {
  id: string
  booking_id: string | null
  status: 'draft' | 'approved' | 'sent' | 'cancelled' | 'superseded'
  draft_purpose: string
  room_code_snapshot: string | null
  guest_display_snapshot: string | null
  created_at: string
  // D6 — approve-to-send review fields (optional: not all selected in every query)
  conversation_id?: string | null
  internal_ops_case_id?: string | null
  channel_target?: string | null
  delivery_mode?: string | null
  draft_text?: string | null
  approval_required?: boolean | null
  auto_send_allowed?: boolean | null
  draft_importance?: string | null
  draft_trigger?: string | null
  reason?: string | null
  visible_context_summary?: string | null
  evidence_summary?: string | null
  latest_guest_message_excerpt?: string | null
  admin_action_needed?: string | null
  platform_snapshot?: string | null
  reservation_number_snapshot?: string | null
  approved_by?: string | null
  approved_at?: string | null
}

// Conversation automation/takeover state (D6) — is the bot replying or paused for admin?
export interface Conversation {
  id: string
  booking_id: string | null
  channel: string | null
  status: string | null
  automation_mode: string | null
  bot_paused_at: string | null
  bot_pause_reason: string | null
  handoff_state: string | null
  risk_level: string | null
  latest_intent: string | null
}

// Outbound send evidence (D6) — proof a draft/message actually went out.
export interface OutboundMessage {
  id: string
  message_draft_id: string | null
  booking_id: string | null
  target_channel: string | null
  send_status: string | null
  approval_status: string | null
  sent_at: string | null
  delivered_at: string | null
  error: string | null
  created_at: string | null
}

// ── Booking evidence drafts (D5) — screenshot/OCR → reviewable booking draft (read-only) ──
// Extracted fields live inside extracted_json (JSONB). `booking_id` there is the PLATFORM's
// reservation reference, NOT our internal booking id — never link it as an internal record.
export interface ExtractedBooking {
  guest_name?: string | null
  platform?: string | null
  booking_id?: string | null
  property_name?: string | null
  room_number?: string | null
  check_in_date?: string | null
  check_out_date?: string | null
  nights?: number | null
  number_of_guests?: number | null
  guest_country?: string | null
  rate_text?: string | null
  notes?: string | null
  confidence?: string | null
  [k: string]: unknown
}

export interface BookingDraft {
  id: string
  session_id: string | null
  source_type: string | null
  platform: string | null
  raw_input_ref: string | null
  extracted_json: ExtractedBooking | null
  extraction_confidence: number | null
  status: string | null
  admin_notes: string | null
  approved_booking_id: string | null
  created_at: string | null
  updated_at: string | null
}

// ── Housekeeping (D4) — cleaning task queue + exception checklist (read-only) ──
// Table is populated by the system even during the DIY period (ADR-0006); Bond + Mom
// view it through Internal Ops. Tolerant fetches mean a not-yet-migrated env shows
// the "ยังไม่เชื่อมต่อ" state instead of breaking.
export interface CleaningTask {
  id: string
  room_id: string | null
  booking_id: string | null
  task_type: string | null
  priority: string | null
  status: string | null
  checklist_status: string | null
  checkin_risk_level: string | null
  requires_admin_attention: boolean | null
  due_at: string | null
  planned_start_at: string | null
  room_ready_at: string | null
  completed_at: string | null
  instructions: string | null
  blocker_reason: string | null
  created_at: string | null
  updated_at: string | null
  // joined from rooms (never raw room_id in the UI)
  room_code?: string | null
  building?: string | null
}

export interface CleaningChecklistItem {
  id: string
  cleaning_task_id: string | null
  room_id: string | null
  item_key: string | null
  item_label: string | null
  required: boolean | null
  status: string | null
  issue_note: string | null
  exception_reason: string | null
}

// ── Event Calendar (D7) — published events that may overlap a guest's stay ──
// Table is 404 until migrated; all loaders return [] on error (tolerant pattern).
// Only published events are guest-facing; draft/pending events are never surfaced here.
export interface EventCalendar {
  id: string
  event_name: string | null
  event_type: string | null   // concert / exam / expo / conference / other
  venue: string | null
  start_date: string | null   // ISO date string
  end_date: string | null
  status: string | null       // published / draft / cancelled
  soft_question_template: string | null
  visitor_hint: string | null // visitor / staff / unknown
  notes: string | null
  created_at: string | null
}

// Guest context tags (D7) — repeat interest signals attached to a guest record.
// Tolerant: if guest_tags is 404, section renders honest empty state.
export interface GuestTag {
  id: string
  booking_id: string | null
  tag_key: string | null      // e.g. concert_visitor, exam_guest, repeat_guest
  tag_label: string | null    // human-readable Thai label (preferred over tag_key)
  source: string | null       // system / admin / ai
  created_at: string | null
}

// Guest notes (D7) — admin context notes attached to a booking.
export interface GuestNote {
  id: string
  booking_id: string | null
  note_text: string | null
  note_type: string | null    // context / preference / caution
  created_by: string | null
  created_at: string | null
}

// ── D7 label maps ──

export const EVENT_TYPE_LABEL: Record<string, string> = {
  concert:    'คอนเสิร์ต',
  exam:       'สอบ',
  expo:       'งานแสดงสินค้า',
  conference: 'ประชุม/สัมมนา',
  sport:      'กีฬา',
  other:      'งานอีเวนต์',
}

export function eventTypeLabel(t: string | null | undefined): string {
  if (!t) return 'งานอีเวนต์'
  return EVENT_TYPE_LABEL[t] ?? 'งานอีเวนต์'  // never leak raw enum
}

export const GUEST_TAG_LABEL: Record<string, string> = {
  concert_visitor: 'แขกดูคอนเสิร์ต',
  exam_guest:      'แขกสอบ',
  repeat_guest:    'แขกกลับมา',
  staff_candidate: 'สัมภาษณ์/พนักงาน',
  exhibitor:       'ผู้แสดงสินค้า',
  long_stay:       'พักยาว',
  foreign_guest:   'แขกต่างชาติ',
}

// Prefer the DB's tag_label (already Thai); fall back to known key, then neutral.
export function guestTagLabel(tag: GuestTag): string {
  if (tag.tag_label) return tag.tag_label
  if (tag.tag_key && GUEST_TAG_LABEL[tag.tag_key]) return GUEST_TAG_LABEL[tag.tag_key]
  return 'แท็กบริบทแขก'
}

// Return published events whose date range overlaps the booking's stay dates.
// Only published events — draft/pending are never surfaced per product rule.
export function overlappingEvents(booking: Booking, events: EventCalendar[]): EventCalendar[] {
  return events.filter(e => {
    if (e.status !== 'published') return false
    if (!e.start_date || !e.end_date) return false
    // overlap: event starts before booking ends AND event ends after booking starts
    return e.start_date < booking.check_out_date && e.end_date > booking.check_in_date
  })
}

export type TabView = 'today' | 'calendar' | 'rooms' | 'upcoming'

export const BUILDING_ORDER = ['C5', 'C4', 'C3', 'C9', 'C8', 'C2', 'T8', 'T9', 'P2']

export const PORTFOLIO_BUILDINGS: Record<Portfolio, string[]> = {
  bond: ['C3', 'C4', 'C5', 'C9'],
  mom: ['C2', 'C8', 'T8', 'T9', 'P2'],
}

// ── Internal Ops case label maps (D2 Case Detail) ──
export const CASE_STATUS_LABEL: Record<string, string> = {
  new:                  'ใหม่',
  triaged:              'จัดประเภทแล้ว',
  waiting_admin:        'รอแอดมิน',
  waiting_guest:        'รอลูกค้า',
  waiting_housekeeping: 'รอแม่บ้าน',
  waiting_platform:     'รอแพลตฟอร์ม',
  scheduled_followup:   'รอติดตามผล',
  resolved:             'แก้แล้ว',
  closed:               'ปิดแล้ว',
}

export const PRIORITY_FULL_LABEL: Record<string, string> = {
  urgent: 'ด่วนมาก',
  high:   'ด่วน',
  normal: 'ปกติ',
  low:    'ไม่ด่วน',
}

export const CHANNEL_LABEL: Record<string, string> = {
  guest_oa:        'LINE ลูกค้า',
  internal_ops_oa: 'LINE Internal',
  housekeeping_line: 'LINE แม่บ้าน',
}

export const CASE_TYPE_LABEL: Record<string, string> = {
  housekeeping:        'ห้องยังไม่พร้อม',
  late_checkout:       'Late checkout — ยังไม่ออก',
  guest_complaint:     'แขกร้องเรียน',
  guest_communication: 'แขกมีเรื่องแจ้ง',
  maintenance_needed:  'ต้องซ่อมแซม',
  no_show:             'No-show',
  disputed_booking:    'จองขัดแย้ง',
  cleaning_overdue:    'ทำความสะอาดล่าช้า',
  guest_issue:         'แขกมีปัญหา',
  concierge_request:   'แขกขอความช่วยเหลือ',
}

const AI_CONCIERGE_SLUG_LABEL: Record<string, string> = {
  guest_waiting_room_not_ready: 'แขกรอห้อง — ยังไม่พร้อม',
  room_not_ready:               'ห้องยังไม่พร้อม',
  late_checkout_pending:        'รอ late checkout ยืนยัน',
}

// Turn raw AI/system slugs into human Thai; keep admin-facing text readable, no backend slugs.
export function sanitizeIssueSummary(text: string | null | undefined): string | null {
  if (!text) return null
  const prefix = 'Guest Concierge ต้องให้แอดมินช่วยตรวจสอบ:'
  if (text.startsWith(prefix)) {
    const slug = text.slice(prefix.length).trim()
    return AI_CONCIERGE_SLUG_LABEL[slug] ?? text.replace(prefix, 'ตรวจสอบ:').trim()
  }
  return text
}

// ── Canonical status system — one source of truth for label + color across every view ──
export const STATUS_LABEL: Record<string, string> = {
  occupied: 'พักอยู่',
  upcoming: 'จะเข้าพัก',
  cleaning: 'ทำความสะอาด',
  vacant:   'ว่าง',
  monthly:  'รายเดือน',
}

export const STATUS_DOT: Record<string, string> = {
  occupied: 'bg-green-500',
  upcoming: 'bg-blue-500',
  cleaning: 'bg-amber-500',
  vacant:   'bg-gray-300',
  monthly:  'bg-gray-500',
}

export const STATUS_TEXT: Record<string, string> = {
  occupied: 'text-green-600',
  upcoming: 'text-blue-600',
  cleaning: 'text-amber-600',
  vacant:   'text-gray-400',
  monthly:  'text-gray-600',
}

export function getStatusColor(status: BookingStatus | null, cleaning: CleaningStatus | null): string {
  if (status === 'checked_in') return 'occupied'
  if (status === 'checked_out' && cleaning !== 'clean') return 'cleaning'
  if (status === 'confirmed') return 'upcoming'
  if (status === 'cancelled' || status === 'no_show') return 'vacant'
  return 'vacant'
}

// Single source of truth for a room's status TODAY — used by Today, Rooms, and Calendar
// so the four status counts always agree. Considers the active booking + cleaning state.
export function getRoomStatusToday(
  room: Room,
  bookings: Booking[],
  roomStatuses: RoomStatus[],
): string {
  const today = new Date().toISOString().slice(0, 10)
  const booking = bookings.find(
    b =>
      b.room_id === room.id &&
      !['cancelled', 'no_show', 'draft'].includes(b.booking_status) &&
      b.check_in_date <= today &&
      b.check_out_date > today,
  )
  const rs = roomStatuses.find(s => s.room_id === room.id)
  if (!booking) {
    if (rs?.cleaning_status === 'dirty' || rs?.cleaning_status === 'cleaning_in_progress') return 'cleaning'
    return 'vacant'
  }
  return getStatusColor(booking.booking_status, rs?.cleaning_status ?? null)
}

// ── Evidence language helpers (Topic C: never claim a guest hasn't arrived) ──

export function checkInEvidence(stay: GuestStayState | undefined | null): string {
  if (!stay) return 'ยังไม่มีสัญญาณ check-in'
  if (stay.check_in_signal_status === 'guest_reported_checked_in' || stay.journey_stage === 'in_room')
    return 'แจ้งเข้าห้องแล้ว'
  if (stay.room_access_package_status && stay.room_access_package_status !== 'not_sent')
    return 'ส่ง room access แล้ว · ยังไม่มีสัญญาณ check-in'
  return 'ยังไม่มีสัญญาณ check-in'
}

export function checkOutEvidence(stay: GuestStayState | undefined | null): string {
  if (stay?.check_out_signal_status === 'guest_reported_checked_out') return 'แจ้ง check-out แล้ว'
  return 'ยังไม่มีสัญญาณ check-out'
}

// ── Room access readiness (D3) — is it safe for Guest OA to send room-entry yet? ──

export const HOLD_REASON_LABEL: Record<string, string> = {
  booking_conflict:   'จองชน/ห้องซ้อน',
  missing_room:       'ยังไม่ได้ระบุห้อง',
  room_not_ready:     'ห้องยังไม่พร้อม',
  needs_recheck:      'รอตรวจสอบความปลอดภัย',
  unverified_booking: 'ยังไม่ได้ยืนยันการจอง',
}

export function verificationLabel(status: string | null | undefined): string {
  if (status === 'confirmed') return 'ยืนยันแล้ว'
  if (status === 'pending_confirmation') return 'รอแขกยืนยัน'
  return 'ยังไม่ยืนยัน'
}

export function packageStatusLabel(status: string | null | undefined): string {
  if (status === 'room_code_sent') return 'ส่งรหัสห้องแล้ว'
  if (status && status !== 'not_sent') return 'อยู่ระหว่างดำเนินการ' // unknown enum — never leak raw value
  return 'ยังไม่ส่ง'
}

export interface BookingAccessPreparation {
  id: string
  booking_id: string
  room_id: string | null
  key_placed_in_room: boolean
  key_placed_at: string | null
  key_placed_by: string | null
  room_left_unlocked_or_open: boolean
  room_opened_at: string | null
  room_opened_by: string | null
  note: string | null
  status: 'not_started' | 'partial' | 'complete' | 'blocked'
  created_at: string | null
  updated_at: string | null
}

export interface RoomAccessVerdict {
  level: 'safe' | 'blocked' | 'caution'
  headline: string
  reasons: string[]
}

export interface RoomAccessReadiness {
  ready: boolean
  booking_id: string
  room_id: string | null
  booking_verified: boolean
  room_assignment_stable: boolean
  cleaning_ready: boolean
  access_prep_ready: boolean
  active_access_incident: boolean
  approved_access_content: boolean
  blockers: string[]
}

export function roomAccessVerdict(
  booking: Booking,
  stay: GuestStayState | undefined | null,
  hold: RoomAccessHold | undefined | null,
  accessPrep: BookingAccessPreparation | undefined | null,
): RoomAccessVerdict {
  const reasons: string[] = []
  if (hold) {
    const r = hold.hold_reason ? HOLD_REASON_LABEL[hold.hold_reason] : null
    reasons.push(r ? `ติด Room Access Hold: ${r}` : 'ติด Room Access Hold')
  }
  if (booking.cleaning_status !== 'clean') {
    reasons.push(!booking.cleaning_status || booking.cleaning_status === 'unknown'
      ? 'ยังไม่ทราบความพร้อมห้อง'
      : 'ห้องยังไม่พร้อม')
  }
  const ver = stay?.booking_verification_status
  if (ver !== 'confirmed') {
    reasons.push(ver === 'pending_confirmation' ? 'แขกยังไม่ยืนยันการจอง' : 'ยังไม่ได้ยืนยันการจอง')
  }
  if (!accessPrep) {
    reasons.push('ยังไม่มีข้อมูล Access Prep ในระบบ')
  } else {
    if (accessPrep.status === 'blocked') {
      reasons.push(`Access Prep ติดปัญหา: ${accessPrep.note ?? 'ไม่ได้ระบุสาเหตุ'}`)
    } else {
      if (!accessPrep.key_placed_in_room) {
        reasons.push('ยังไม่ได้วางกุญแจในห้อง')
      }
      if (!accessPrep.room_left_unlocked_or_open) {
        reasons.push('ยังไม่ได้เปิดห้องหรือทิ้งปลดล็อกไว้')
      }
    }
  }
  if (reasons.length) {
    const hasCoreBlockers = hold || booking.cleaning_status !== 'clean' || ver !== 'confirmed'
    const hasPrepBlocker = accessPrep?.status === 'blocked'
    if (hasCoreBlockers || hasPrepBlocker) {
      return { level: 'blocked', headline: 'ยังไม่ปลอดภัยที่จะส่งวิธีเข้าห้อง', reasons }
    }
    return { level: 'caution', headline: 'รอเตรียมความพร้อมกุญแจและห้อง', reasons }
  }
  return {
    level: 'safe',
    headline: 'พร้อมส่งวิธีเข้าห้องแล้ว',
    reasons: ['ห้องทำความสะอาดแล้ว ยืนยันจองแล้ว และวางกุญแจเปิดห้องเรียบร้อย'],
  }
}

// ── Housekeeping helpers (D4) ──

export const CLEANING_TASK_STATUS_LABEL: Record<string, string> = {
  pending:     'รอเริ่ม',
  queued:      'รอคิว',
  assigned:    'มอบหมายแล้ว',
  in_progress: 'กำลังทำ',
  blocked:     'ติดปัญหา',
  done:        'เสร็จแล้ว',
  completed:   'เสร็จแล้ว',
  verified:    'ตรวจแล้ว',
  cancelled:   'ยกเลิก',
}

// Launch exception checklist — canonical Thai labels used only when the row has no
// item_label. The 6 required items: ทำความสะอาด, ผ้าปูที่นอน, ผ้าขนหนู, น้ำ, ทิชชู่, สบู่.
export const CHECKLIST_ITEM_LABEL: Record<string, string> = {
  room_cleaned: 'ทำความสะอาด',
  cleaning:     'ทำความสะอาด',
  bedsheet:     'ผ้าปูที่นอน',
  bedsheet_set: 'ผ้าปูที่นอน',
  linen:        'ผ้าปูที่นอน',
  towel:        'ผ้าขนหนู',
  water:        'น้ำ',
  tissue:       'ทิชชู่',
  soap:         'สบู่',
}

export function cleaningTaskStatusLabel(status: string | null | undefined): string {
  if (!status) return 'รอเริ่ม'
  return CLEANING_TASK_STATUS_LABEL[status] ?? 'อยู่ระหว่างดำเนินการ' // never leak a raw enum
}

// Prefer the DB's item_label (already Thai); fall back to a known key, then a neutral label.
export function checklistItemLabel(item: CleaningChecklistItem): string {
  if (item.item_label) return item.item_label
  if (item.item_key && CHECKLIST_ITEM_LABEL[item.item_key]) return CHECKLIST_ITEM_LABEL[item.item_key]
  return 'รายการตรวจ'
}

// Relative due-time for a cleaning task. Read-only; null when no due time is set.
export function dueLabel(dueAt: string | null | undefined, now: Date = new Date()): string | null {
  if (!dueAt) return null
  const due = new Date(dueAt)
  if (isNaN(due.getTime())) return null
  const diffMin = Math.round((due.getTime() - now.getTime()) / 60000)
  if (diffMin < 0) return 'เลยกำหนดแล้ว'
  if (diffMin < 60) return `ภายใน ${diffMin} นาที`
  const hrs = Math.round(diffMin / 60)
  if (hrs < 24) return `ภายใน ${hrs} ชม.`
  return due.toLocaleDateString('th-TH', { day: 'numeric', month: 'short' })
}

// ── Booking evidence draft helpers (D5) ──

export const DRAFT_REVIEW_STATUS_LABEL: Record<string, string> = {
  pending:      'รอตรวจ',
  needs_review: 'ต้องตรวจเพิ่ม',
  approved:     'อนุมัติแล้ว',
  confirmed:    'ยืนยันแล้ว',
  rejected:     'ปฏิเสธ',
  superseded:   'ถูกแทนที่',
}

export function draftReviewStatusLabel(status: string | null | undefined): string {
  if (!status) return 'รอตรวจ'
  return DRAFT_REVIEW_STATUS_LABEL[status] ?? 'อยู่ระหว่างดำเนินการ' // never leak a raw enum
}

// Coerce an arbitrary OCR/platform string into the known Platform union (unknown → 'other').
export function normalizePlatform(p: string | null | undefined): Platform {
  const known: Platform[] = ['booking', 'agoda', 'airbnb', 'line', 'direct', 'other']
  return (p && (known as string[]).includes(p)) ? (p as Platform) : 'other'
}

// ── Approve-to-send draft review helpers (D6) ──

// Channel target may be an internal LINE channel OR a platform inbox to copy-paste into.
export function channelTargetLabel(ch: string | null | undefined): string {
  if (!ch) return 'ไม่ระบุช่องทาง'
  if (CHANNEL_LABEL[ch]) return CHANNEL_LABEL[ch]
  const plat: Platform[] = ['booking', 'agoda', 'airbnb', 'line', 'direct']
  if ((plat as string[]).includes(ch)) return platformLabel(ch as Platform)
  return 'ช่องทางอื่น' // never leak a raw enum
}

// How the message is delivered — copy-paste by admin vs system push.
export function deliveryModeLabel(mode: string | null | undefined): string {
  switch (mode) {
    case 'admin_copy_paste': return 'ต้อง copy-paste ส่งเอง'
    case 'push':
    case 'auto_send':
    case 'line_push':        return 'ระบบส่งให้อัตโนมัติ'
    case 'admin_assisted':   return 'แอดมินกดส่ง'
    default:                 return mode ? 'อยู่ระหว่างดำเนินการ' : '—'
  }
}

export const MSG_DRAFT_STATUS_LABEL: Record<string, string> = {
  draft:      'รออนุมัติ',
  approved:   'อนุมัติแล้ว',
  sent:       'ส่งแล้ว',
  cancelled:  'ยกเลิก',
  superseded: 'ถูกแทนที่',
}

export function msgDraftStatusLabel(status: string | null | undefined): string {
  if (!status) return 'รออนุมัติ'
  return MSG_DRAFT_STATUS_LABEL[status] ?? 'อยู่ระหว่างดำเนินการ'
}

export function draftImportanceLabel(imp: string | null | undefined): string {
  switch (imp) {
    case 'risky':     return 'ต้องระวัง'
    case 'important': return 'สำคัญ'
    case 'routine':   return 'ทั่วไป'
    default:          return imp ? 'ทั่วไป' : '—'
  }
}

export function sendStatusLabel(status: string | null | undefined): string {
  switch (status) {
    case 'sent':      return 'ส่งแล้ว'
    case 'delivered': return 'ถึงผู้รับแล้ว'
    case 'failed':    return 'ส่งไม่สำเร็จ'
    case 'queued':    return 'รอส่ง'
    case 'pending':   return 'รอส่ง'
    default:          return status ? 'อยู่ระหว่างดำเนินการ' : '—'
  }
}

export interface BotState {
  active: boolean
  label: string
  risk: string | null
}

// Is the bot still auto-replying in this conversation, or paused for admin takeover?
export function conversationBotState(conv: Conversation | null | undefined): BotState {
  const risk = conv?.risk_level && conv.risk_level !== 'normal' ? conv.risk_level : null
  if (!conv) return { active: true, label: 'บอทตอบอัตโนมัติ', risk: null }
  const paused = conv.bot_paused_at != null || conv.automation_mode === 'paused' || conv.handoff_state === 'admin'
  return {
    active: !paused,
    label: paused ? 'แอดมินรับเองอยู่ (บอทหยุด)' : 'บอทตอบอัตโนมัติ',
    risk,
  }
}

export interface ConfidenceBand {
  level: 'high' | 'medium' | 'low'
  label: string
}

// extraction_confidence is 0–100. Bands keep the UI honest about how much to trust OCR.
export function confidenceBand(score: number | null | undefined): ConfidenceBand {
  const s = typeof score === 'number' ? score : 0
  if (s >= 80) return { level: 'high', label: `มั่นใจสูง ${s}%` }
  if (s >= 50) return { level: 'medium', label: `มั่นใจปานกลาง ${s}%` }
  return { level: 'low', label: `มั่นใจต่ำ ${s}%` }
}

// Required canonical fields for a real booking — which are still missing in the draft?
export function missingDraftFields(j: ExtractedBooking | null | undefined): string[] {
  const need: [keyof ExtractedBooking, string][] = [
    ['guest_name', 'ชื่อแขก'],
    ['check_in_date', 'วันเช็กอิน'],
    ['check_out_date', 'วันเช็กเอาต์'],
    ['room_number', 'ห้อง'],
    ['platform', 'แพลตฟอร์ม'],
  ]
  if (!j) return need.map(n => n[1])
  return need.filter(([k]) => j[k] == null || j[k] === '').map(n => n[1])
}

// Lightweight "is this guest already booked?" candidates — same check-in date or matching
// room code. Read-only safety net so admins don't create duplicate bookings.
export function similarBookingCandidates(j: ExtractedBooking | null | undefined, bookings: Booking[]): Booking[] {
  if (!j) return []
  const ci = j.check_in_date ?? null
  const room = (j.room_number ?? '').trim()
  return bookings
    .filter(b => !['cancelled', 'no_show', 'draft'].includes(b.booking_status))
    .filter(b => (ci && b.check_in_date === ci) || (room && b.room_code === room))
    .slice(0, 3)
}

// Room readiness shown for today/tomorrow check-ins. "unknown" stays honest — never assume ready.
export function readinessLabel(cleaning: CleaningStatus | null): string {
  if (cleaning === 'clean') return 'ห้องพร้อม'
  if (cleaning === 'dirty' || cleaning === 'cleaning_in_progress') return 'ห้องยังไม่พร้อม'
  return 'ห้อง: ยังไม่ทราบความพร้อม'
}

// "คืนที่ 2/3" for a guest currently mid-stay
export function nightInfo(checkIn: string, nights: number, todayStr: string): string {
  if (!nights || nights < 1) return ''
  const ci = new Date(checkIn).getTime()
  const t = new Date(todayStr).getTime()
  const elapsed = Math.floor((t - ci) / 86400000)
  const current = Math.min(Math.max(elapsed + 1, 1), nights)
  return `คืนที่ ${current}/${nights}`
}

export function addDaysISO(dateStr: string, days: number): string {
  const d = new Date(dateStr)
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}

export function isToday(dateStr: string): boolean {
  const today = new Date()
  const d = new Date(dateStr)
  return d.getFullYear() === today.getFullYear() &&
    d.getMonth() === today.getMonth() &&
    d.getDate() === today.getDate()
}

export function isTodayOrBefore(dateStr: string): boolean {
  const today = new Date()
  today.setHours(23, 59, 59, 999)
  return new Date(dateStr) <= today
}

export function platformLabel(p: Platform): string {
  const map: Record<Platform, string> = {
    booking: 'Booking.com',
    agoda: 'Agoda',
    airbnb: 'Airbnb',
    line: 'LINE',
    direct: 'Direct',
    other: 'Other',
  }
  return map[p] ?? p
}

const CONFIG_NOISE_SLUGS = [
  'building_location_map_missing',
  'room_entry_asset_missing',
  'listing_incomplete',
  'photo_missing',
  'calendar_not_synced',
  'price_not_set',
]

export function isConfigNoise(a: Alert): boolean {
  const text = `${a.issue_summary ?? ''} ${a.admin_action_needed ?? ''}`
  return CONFIG_NOISE_SLUGS.some(slug => text.includes(slug))
}

export function thaiDate(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('th-TH', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}
