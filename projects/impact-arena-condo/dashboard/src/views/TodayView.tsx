import { CheckCircle2, ChevronRight, ShieldAlert, Sparkles, Camera, KeyRound } from 'lucide-react'
import type { Booking, Alert, MessageDraft, Room, RoomStatus, GuestStayState, RoomAccessHold, CleaningTask, CleaningChecklistItem, BookingDraft, BookingAccessPreparation, AccessPrepTask } from '../lib/types'
import {
  getStatusColor,
  getRoomStatusToday,
  isConfigNoise,
  STATUS_LABEL,
  CASE_TYPE_LABEL,
  sanitizeIssueSummary,
  checkInEvidence,
  checkOutEvidence,
  readinessLabel,
  nightInfo,
  addDaysISO,
  cleaningTaskStatusLabel,
  dueLabel,
  confidenceBand,
  missingDraftFields,
  normalizePlatform,
  checklistItemLabel,
  accessPrepTaskStatusLabel,
  ownerOverrideWarning,
} from '../lib/types'
import { PlatformPill } from '../components/PlatformPill'
import { RoomThumb } from '../components/RoomThumb'

interface Props {
  bookings: Booking[]
  rooms: Room[]
  roomStatuses: RoomStatus[]
  alerts: Alert[]
  drafts: MessageDraft[]
  stayStates: GuestStayState[]
  holds: RoomAccessHold[]
  cleaningTasks: CleaningTask[]
  accessPrepTasks: AccessPrepTask[]
  checklistItems: CleaningChecklistItem[]
  bookingDrafts: BookingDraft[]
  accessPreps: BookingAccessPreparation[]
  lastUpdated: Date | null
  onSelect: (b: Booking) => void
  onSelectCase: (a: Alert) => void
  onSelectDraft: (d: BookingDraft) => void
  onSelectDraftMsg: (d: MessageDraft) => void
}

function formatUpdated(d: Date | null): string {
  if (!d) return ''
  return d.toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' })
}

const PRIORITY_LABEL: Record<string, string> = {
  urgent: 'ด่วนมาก',
  high:   'ด่วน',
}

const DRAFT_PURPOSE_LABEL: Record<string, string> = {
  status_check:           'ตรวจสอบสถานะ',
  check_in_instructions:  'ส่งข้อมูล check-in',
  checkout_reminder:      'แจ้งเตือน checkout',
  review_request:         'ขอรีวิว',
  complaint_followup:     'ติดตามข้อร้องเรียน',
}

// ── Section header: label + count, calm Airbnb hierarchy ──
function SectionHeader({ title, count }: { title: string; count: number }) {
  return (
    <div className="flex items-center gap-2 mb-3 md:mb-4">
      <h2 className="text-[18px] md:text-[20px] font-bold text-[#222222] tracking-tight">{title}</h2>
      <span className="text-[12px] font-semibold text-gray-500 bg-[#F7F7F7] border border-[#EBEBEB] rounded-full px-2.5 py-0.5">
        {count}
      </span>
    </div>
  )
}

// ── Booking row: room + guest + platform, with optional evidence/meta lines (read-only) ──
function BookingRow({
  b,
  onClick,
  meta,
  evidence,
  warn,
  index = 0,
}: {
  b: Booking
  onClick: () => void
  meta?: string
  evidence?: string
  warn?: string
  index?: number
}) {
  const color = getStatusColor(b.booking_status, b.cleaning_status)
  return (
    <button
      onClick={onClick}
      style={{ ['--i' as string]: index } as React.CSSProperties}
      className="animate-riseIn w-full bg-white border border-[#EBEBEB] rounded-[24px] p-4 md:p-5 shadow-sm active:scale-[0.98] hover:border-gray-300 transition-all text-left flex items-start gap-4"
    >
      <RoomThumb color={color} photoUrl={b.photo_url ?? undefined} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="font-semibold text-[16px] text-[#222222] truncate">
            {b.room_code ?? 'ไม่ระบุห้อง'}
          </span>
          <PlatformPill platform={b.platform} />
        </div>
        <p className="text-[13px] text-gray-500 truncate mt-0.5">{b.guest_name_snapshot}</p>
        {warn && (
          <p className="inline-flex items-center gap-1 text-[12px] font-medium text-red-600 mt-1">
            <ShieldAlert size={12} className="flex-shrink-0" />
            {warn}
          </p>
        )}
        {(meta || evidence) && (
          <p className="text-[12px] text-gray-400 mt-0.5 leading-snug whitespace-normal break-words">
            {[meta, evidence].filter(Boolean).join(' · ')}
          </p>
        )}
      </div>
      <ChevronRight size={18} className="text-gray-300 flex-shrink-0 mt-2.5" />
    </button>
  )
}

// ── Case row (lightweight, read-only): code + priority + room/guest + reason + suggested action ──
function CaseRow({ a, onClick, index = 0 }: { a: Alert; onClick: () => void; index?: number }) {
  const title =
    a.room_code_snapshot ??
    a.guest_display_snapshot ??
    CASE_TYPE_LABEL[a.case_type] ??
    'เคส'
  const reason = sanitizeIssueSummary(a.issue_summary) ?? CASE_TYPE_LABEL[a.case_type] ?? null
  const nextAction = a.ai_suggestion ?? a.admin_action_needed
  const showPriority = a.priority === 'urgent' || a.priority === 'high'
  const guestLine = a.room_code_snapshot ? a.guest_display_snapshot : null

  return (
    <button
      onClick={onClick}
      className="animate-riseIn w-full bg-white border border-[#EBEBEB] rounded-[24px] p-4 md:p-5 shadow-sm active:scale-[0.98] hover:border-gray-300 transition-all text-left flex items-start gap-4"
      style={{ ['--i' as string]: index } as React.CSSProperties}
    >
      <div className="w-10 h-10 rounded-full bg-red-50 flex items-center justify-center flex-shrink-0 text-red-500 mt-0.5">
        <span className={`w-3 h-3 rounded-full bg-red-500 ${showPriority ? 'animate-pulseRing' : ''}`} />
      </div>
      <div className="flex-1 min-w-0">
        {showPriority && (
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="bg-red-50 text-red-600 border border-red-100 rounded-full px-2.5 py-0.5 text-[11px] font-semibold flex-shrink-0">
              {PRIORITY_LABEL[a.priority]}
            </span>
          </div>
        )}
        <span className="font-semibold text-[16px] text-[#222222] block leading-tight">
          {title}
        </span>
        {guestLine && <p className="text-[13px] text-gray-500 mt-1 truncate">{guestLine}</p>}
        {reason && <p className="text-[13px] text-gray-500 mt-1 whitespace-normal break-words leading-relaxed">{reason}</p>}
        {nextAction && (
          <p className="text-[12px] text-gray-400 mt-1.5 whitespace-normal break-words leading-relaxed">แนะนำ: {nextAction}</p>
        )}
      </div>
      <ChevronRight size={18} className="text-gray-300 flex-shrink-0 mt-3" />
    </button>
  )
}

function DraftRow({ d, onClick, index = 0 }: { d: MessageDraft; onClick: () => void; index?: number }) {
  return (
    <button
      onClick={onClick}
      className="animate-riseIn w-full bg-white border border-[#EBEBEB] rounded-[24px] p-4 md:p-5 shadow-sm active:scale-[0.98] hover:border-gray-300 transition-all text-left flex items-start gap-4"
      style={{ ['--i' as string]: index } as React.CSSProperties}
    >
      <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center flex-shrink-0 text-amber-500">
        <span className="w-3 h-3 rounded-full bg-amber-500" />
      </div>
      <div className="flex-1 min-w-0">
        <span className="font-semibold text-[16px] text-[#222222] truncate block">
          {d.room_code_snapshot ?? d.guest_display_snapshot ?? 'Draft'} — รออนุมัติ
        </span>
        <p className="text-[13px] text-gray-500 mt-0.5">
          {DRAFT_PURPOSE_LABEL[d.draft_purpose] ?? d.draft_purpose}
        </p>
      </div>
      <ChevronRight size={18} className="text-gray-300 flex-shrink-0 mt-2.5" />
    </button>
  )
}

// ── Cleaning task row (D4, read-only): room/building badge + status + due + checklist progress ──
function CleaningRow({
  t,
  checklist,
  missingItems,
  onClick,
  index = 0,
}: {
  t: CleaningTask
  checklist: { done: number; total: number }
  missingItems: string[]
  onClick?: () => void
  index?: number
}) {
  const urgent = t.priority === 'urgent' || t.priority === 'high' || t.checkin_risk_level === 'high'
  const due = dueLabel(t.due_at)
  const overdue = due === 'เลยกำหนดแล้ว'
  const meta = [
    cleaningTaskStatusLabel(t.status),
    checklist.total > 0 ? `เช็กลิสต์ ${checklist.done}/${checklist.total}` : null,
    due,
  ].filter(Boolean).join(' · ')

  return (
    <button
      onClick={onClick}
      disabled={!onClick}
      style={{ ['--i' as string]: index } as React.CSSProperties}
      className={`animate-riseIn w-full bg-white border border-[#EBEBEB] rounded-[24px] p-4 md:p-5 shadow-sm text-left flex items-start gap-4 transition-all ${
        onClick ? 'active:scale-[0.98] hover:border-gray-300' : 'cursor-default'
      }`}
    >
      <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center flex-shrink-0 text-amber-500">
        <span className={`w-3 h-3 rounded-full bg-amber-500 ${urgent ? 'animate-pulseRing' : ''}`} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-semibold text-[16px] text-[#222222] truncate">
            {t.room_code ?? 'ไม่ระบุห้อง'}
          </span>
          {t.building && (
            <span className="text-[11px] text-gray-400 bg-gray-100 rounded px-1.5 py-0.5 flex-shrink-0">
              {t.building}
            </span>
          )}
        </div>
        <p className={`text-[12px] mt-0.5 leading-snug whitespace-normal break-words ${overdue ? 'text-red-600 font-medium' : 'text-gray-400'}`}>
          {meta}
        </p>
        {missingItems.length > 0 && (
          <p className="text-[12px] text-red-600 font-medium mt-0.5">
            ขาด: {missingItems.join(' · ')}
          </p>
        )}
        {t.blocker_reason && (
          <p className="text-[12px] text-red-600 mt-0.5 whitespace-normal break-words">ติดปัญหา: {t.blocker_reason}</p>
        )}
      </div>
      {onClick && <ChevronRight size={18} className="text-gray-300 flex-shrink-0 mt-2.5" />}
    </button>
  )
}

function AccessPrepRow({
  task,
  linkedCleaning,
  index = 0,
}: {
  task: AccessPrepTask
  linkedCleaning: CleaningTask | undefined
  index?: number
}) {
  const due = dueLabel(task.due_at ?? task.scheduled_for)
  const warning = ownerOverrideWarning(task)
  return (
    <div
      style={{ ['--i' as string]: index } as React.CSSProperties}
      className="animate-riseIn w-full bg-white border border-[#EBEBEB] rounded-[24px] p-4 md:p-5 shadow-sm flex items-start gap-4"
    >
      <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0 text-blue-600">
        <KeyRound size={18} />
      </div>
      <div className="flex-1 min-w-0">
        <span className="font-semibold text-[16px] text-[#222222] block truncate">
          {task.room_code ?? 'ไม่ระบุห้อง'}
        </span>
        <p className="text-[12px] text-gray-500 mt-0.5 leading-snug">
          {[accessPrepTaskStatusLabel(task.status), due, `กุญแจ: ${task.key_custody === 'placed_in_room' ? 'วางในห้องแล้ว' : task.key_custody === 'with_owner' ? 'อยู่กับเจ้าของ' : task.key_custody === 'with_operator' ? 'อยู่กับผู้ปฏิบัติงาน' : 'ยังไม่ระบุ'}`].filter(Boolean).join(' · ')}
        </p>
        <p className="text-[12px] text-gray-400 mt-0.5">
          Cleaning: {linkedCleaning ? cleaningTaskStatusLabel(linkedCleaning.status) : 'ยังไม่มีงานเชื่อมกัน'}
        </p>
        {task.blocker_reason && <p className="text-[12px] text-red-600 mt-0.5">ติดปัญหา: {task.blocker_reason}</p>}
        {warning && (
          <p className="inline-flex items-start gap-1 text-[12px] font-medium text-amber-700 mt-1">
            <ShieldAlert size={12} className="flex-shrink-0 mt-0.5" />
            {warning}
          </p>
        )}
      </div>
    </div>
  )
}

// ── Booking evidence draft row (D5, read-only): guest + platform + confidence + missing ──
function DraftEvidenceRow({ d, onClick, index = 0 }: { d: BookingDraft; onClick: () => void; index?: number }) {
  const j = d.extracted_json ?? null
  const guest = j?.guest_name ?? 'ยังไม่มีชื่อแขก'
  const conf = confidenceBand(d.extraction_confidence)
  const missing = missingDraftFields(j)
  const confClass =
    conf.level === 'high' ? 'text-green-600' : conf.level === 'medium' ? 'text-amber-600' : 'text-red-600'

  return (
    <button
      onClick={onClick}
      style={{ ['--i' as string]: index } as React.CSSProperties}
      className="animate-riseIn w-full bg-white border border-[#EBEBEB] rounded-[24px] p-4 md:p-5 shadow-sm active:scale-[0.98] hover:border-gray-300 transition-all text-left flex items-start gap-4"
    >
      <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0 text-gray-400">
        <Camera size={18} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="font-semibold text-[16px] text-[#222222] truncate">{guest}</span>
          <PlatformPill platform={normalizePlatform(j?.platform ?? d.platform)} />
        </div>
        <p className={`text-[12px] mt-0.5 font-medium ${confClass}`}>{conf.label}</p>
        <p className="text-[12px] text-gray-400 mt-0.5 leading-snug whitespace-normal break-words">
          {missing.length > 0 ? `ข้อมูลไม่ครบ: ${missing.join(' · ')}` : 'ข้อมูลครบ — รอตรวจยืนยัน'}
        </p>
      </div>
      <ChevronRight size={18} className="text-gray-300 flex-shrink-0 mt-2.5" />
    </button>
  )
}

function StatStrip({
  occupied,
  upcoming,
  cleaning,
  vacant,
}: {
  occupied: number
  upcoming: number
  cleaning: number
  vacant: number
}) {
  const items = [
    { label: 'พักอยู่', count: occupied, dot: 'bg-[#008A05]' },
    { label: 'จะเข้า', count: upcoming, dot: 'bg-[#1066D6]' },
    { label: 'ทำสะอาด', count: cleaning, dot: 'bg-[#B27600]' },
    { label: 'ห้องว่าง', count: vacant, dot: 'bg-[#717171]' },
  ]
  return (
    <div className="bg-white border border-[#EBEBEB] rounded-[24px] py-4 shadow-sm grid grid-cols-4 mt-6">
      {items.map((item, idx) => (
        <div
          key={item.label}
          className={`flex flex-col items-center justify-center text-center px-1 md:px-2 ${
            idx < items.length - 1 ? 'border-r border-[#EBEBEB]' : ''
          }`}
        >
          <div className="flex items-center gap-1.5 justify-center">
            <span className="text-[18px] md:text-[22px] font-extrabold text-[#222222] leading-none">
              {item.count}
            </span>
            <span className={`w-1.5 h-1.5 md:w-2 md:h-2 rounded-full flex-shrink-0 ${item.dot}`} />
          </div>
          <span className="text-[11px] md:text-[12px] font-semibold text-[#717171] mt-1.5 leading-none">
            {item.label}
          </span>
        </div>
      ))}
    </div>
  )
}


export function TodayView({ bookings, rooms, roomStatuses, alerts, drafts, stayStates, holds, cleaningTasks, accessPrepTasks, checklistItems, bookingDrafts, accessPreps, lastUpdated, onSelect, onSelectCase, onSelectDraft, onSelectDraftMsg }: Props) {
  const today = new Date().toISOString().slice(0, 10)
  const tomorrow = addDaysISO(today, 1)
  const activeAccessPrepTasks = accessPrepTasks.filter(task => !['done', 'canceled'].includes(task.status))

  const stayByBooking = new Map<string, GuestStayState>()
  for (const s of stayStates) if (s.booking_id) stayByBooking.set(s.booking_id, s)

  const accessPrepByBooking = new Map<string, BookingAccessPreparation>()
  for (const ap of accessPreps) if (ap.booking_id) accessPrepByBooking.set(ap.booking_id, ap)

  // Active room-access holds, keyed by booking — surfaces "ติด Room Access Hold" on the row
  const heldBookings = new Set<string>()
  for (const h of holds) if (h.booking_id) heldBookings.add(h.booking_id)

  // Checklist progress per cleaning task (done / total) — read-only preview counts
  const checklistByTask = new Map<string, { done: number; total: number }>()
  const missingItemsByTask = new Map<string, string[]>()
  for (const it of checklistItems) {
    if (!it.cleaning_task_id) continue
    const c = checklistByTask.get(it.cleaning_task_id) ?? { done: 0, total: 0 }
    c.total += 1
    if (it.status === 'present' || it.status === 'done' || it.status === 'completed' || it.status === 'ok') {
      c.done += 1
    } else if (it.status === 'missing') {
      const arr = missingItemsByTask.get(it.cleaning_task_id) ?? []
      arr.push(checklistItemLabel(it))
      missingItemsByTask.set(it.cleaning_task_id, arr)
    }
    checklistByTask.set(it.cleaning_task_id, c)
  }
  const checklistFor = (taskId: string) => checklistByTask.get(taskId) ?? { done: 0, total: 0 }

  // Booking evidence drafts awaiting review (read-only) — only the un-actioned ones
  const pendingDrafts = bookingDrafts.filter(d => d.status === 'pending' || d.status === 'needs_review')

  // Needs-care: ops alerts (config noise filtered) + drafts pending approval
  const opsAlerts = alerts.filter(a => !isConfigNoise(a))
  const sortedAlerts = [...opsAlerts].sort((a, b) => {
    const rank: Record<string, number> = { urgent: 0, high: 1, normal: 2, low: 3 }
    return (rank[a.priority] ?? 2) - (rank[b.priority] ?? 2)
  })

  const active = bookings.filter(
    b => !['cancelled', 'no_show', 'draft'].includes(b.booking_status),
  )

  // Operational sections — no overlap: arrivals / mid-stay / departures / tomorrow
  const checkInsToday = active.filter(b => b.check_in_date === today)
  const checkOutsToday = active.filter(b => b.check_out_date === today && b.check_in_date !== today)
  const currentStays = active.filter(b => b.check_in_date < today && b.check_out_date > today)
  const tomorrowCheckIns = active.filter(b => b.check_in_date === tomorrow)

  // Housekeeping queue (read-only, derived) — checkout done but room not yet clean
  const needsCleaning = active.filter(
    b =>
      b.booking_status === 'checked_out' &&
      (b.cleaning_status === 'dirty' || b.cleaning_status === 'cleaning_in_progress') &&
      b.check_out_date <= today,
  )

  // Stat strip — canonical room status today (shared with Rooms + Calendar so counts agree)
  const roomStat = (c: string) =>
    rooms.filter(r => getRoomStatusToday(r, bookings, roomStatuses) === c).length
  const occupied = roomStat('occupied')
  const upcoming = roomStat('upcoming')
  const cleaning = roomStat('cleaning')
  const vacant   = roomStat('vacant')

  const needsCareCount = sortedAlerts.length + drafts.length
  const dayEmpty =
    needsCareCount === 0 &&
    checkInsToday.length === 0 &&
    currentStays.length === 0 &&
    checkOutsToday.length === 0 &&
    tomorrowCheckIns.length === 0 &&
    needsCleaning.length === 0 &&
    cleaningTasks.length === 0 &&
    activeAccessPrepTasks.length === 0 &&
    pendingDrafts.length === 0

  const h1 =
    needsCareCount === 0
      ? 'วันนี้ไม่มีเรื่องต้องดูแล'
      : needsCareCount === 1
      ? 'วันนี้มี 1 เรื่องต้องดูแล'
      : `วันนี้มี ${needsCareCount} เรื่องต้องดูแล`

  // Stagger index — capped so the animation never feels slow on long lists
  let stagger = 0
  const next = () => Math.min(stagger++, 8)

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-8 pb-12">
      {/* Contextual heading */}
      <div className="pt-7">
        <h1
          className="text-[28px] md:text-[36px] font-extrabold text-[#222222] leading-[1.2] tracking-tight"
          style={{ textWrap: 'balance' } as React.CSSProperties}
        >
          {h1}
        </h1>
        {lastUpdated && (
          <p className="text-[12px] text-gray-400 mt-1.5">อัปเดตล่าสุด {formatUpdated(lastUpdated)}</p>
        )}
      </div>

      {/* Stats — canonical status counts */}
      <StatStrip occupied={occupied} upcoming={upcoming} cleaning={cleaning} vacant={vacant} />


      {dayEmpty ? (
        <div className="mt-8">
          <div className="flex flex-col items-center justify-center pt-16 pb-8 gap-4">
            <CheckCircle2 size={48} className="text-gray-200 animate-scaleIn" strokeWidth={1.5} />
            <div className="text-center">
              <p className="text-[16px] font-semibold text-gray-400">ทุกอย่างเรียบร้อย</p>
              <p className="text-[13px] text-gray-300 mt-1">ว่าง {vacant} ห้อง พร้อมรับแขก</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-8 md:grid md:grid-cols-2 md:gap-12">
          {/* Left Column: Needs Care & Booking Drafts */}
          <div className="space-y-8 md:space-y-10">
            {/* 1 — Needs care (urgent first) */}
            {needsCareCount > 0 && (
              <section>
                <SectionHeader title="ต้องดูแล" count={needsCareCount} />
                <div className="mt-2.5 space-y-3">
                  {sortedAlerts.map(a => <CaseRow key={a.id} a={a} onClick={() => onSelectCase(a)} index={next()} />)}
                  {drafts.map(d => <DraftRow key={d.id} d={d} onClick={() => onSelectDraftMsg(d)} index={next()} />)}
                </div>
              </section>
            )}

            {/* 1.5 — Booking evidence drafts awaiting review (D5, read-only) */}
            {pendingDrafts.length > 0 && (
              <section>
                <SectionHeader title="หลักฐานการจองรอตรวจ" count={pendingDrafts.length} />
                <div className="mt-2.5 space-y-3">
                  {pendingDrafts.map(d => (
                    <DraftEvidenceRow key={d.id} d={d} onClick={() => onSelectDraft(d)} index={next()} />
                  ))}
                  <p className="text-[12px] text-gray-400 py-1 pl-1">
                    อนุมัติ/สร้างใบจองในไลน์ Internal — แดชบอร์ดนี้ดูอย่างเดียว
                  </p>
                </div>
              </section>
            )}
          </div>

          {/* Right Column: Stays, Check-ins, Check-outs, Cleaning */}
          <div className="space-y-8 md:space-y-10 mt-10 md:mt-0">
            {/* 2 — Check-ins today (readiness + check-in evidence) */}
            {checkInsToday.length > 0 && (
              <section>
                <SectionHeader title="เช็กอินวันนี้" count={checkInsToday.length} />
                <div className="mt-2.5 space-y-3">
                  {checkInsToday.map(b => {
                    const ap = accessPrepByBooking.get(b.id)
                    const apMeta = ap
                      ? `${ap.key_placed_in_room ? 'วางกุญแจแล้ว' : 'ยังไม่วางกุญแจ'} · ${ap.room_left_unlocked_or_open ? 'เปิดห้องแล้ว' : 'ยังไม่เปิดห้อง'}`
                      : 'ยังไม่ได้เตรียมกุญแจ'
                    return (
                      <BookingRow
                        key={b.id}
                        b={b}
                        onClick={() => onSelect(b)}
                        meta={`${readinessLabel(b.cleaning_status)} · ${apMeta}`}
                        evidence={checkInEvidence(stayByBooking.get(b.id))}
                        warn={heldBookings.has(b.id) ? 'ติด Room Access Hold' : undefined}
                        index={next()}
                      />
                    )
                  })}
                </div>
              </section>
            )}

            {/* 3 — Current stays (mid-stay) */}
            {currentStays.length > 0 && (
              <section>
                <SectionHeader title="พักอยู่" count={currentStays.length} />
                <div className="mt-2.5 space-y-3">
                  {currentStays.map(b => (
                    <BookingRow
                      key={b.id}
                      b={b}
                      onClick={() => onSelect(b)}
                      meta={nightInfo(b.check_in_date, b.nights, today)}
                      warn={heldBookings.has(b.id) ? 'ติด Room Access Hold' : undefined}
                      index={next()}
                    />
                  ))}
                </div>
              </section>
            )}

            {/* 4 — Check-outs today */}
            {checkOutsToday.length > 0 && (
              <section>
                <SectionHeader title="เช็กเอาต์วันนี้" count={checkOutsToday.length} />
                <div className="mt-2.5 space-y-3">
                  {checkOutsToday.map(b => (
                    <BookingRow
                      key={b.id}
                      b={b}
                      onClick={() => onSelect(b)}
                      evidence={checkOutEvidence(stayByBooking.get(b.id))}
                      index={next()}
                    />
                  ))}
                </div>
              </section>
            )}

            {/* 5 — Tomorrow check-ins only (readiness preview) */}
            {tomorrowCheckIns.length > 0 && (
              <section>
                <SectionHeader title="เช็กอินพรุ่งนี้" count={tomorrowCheckIns.length} />
                <div className="mt-2.5 space-y-3">
                  {tomorrowCheckIns.map(b => (
                    <BookingRow
                      key={b.id}
                      b={b}
                      onClick={() => onSelect(b)}
                      meta={readinessLabel(b.cleaning_status)}
                      index={next()}
                    />
                  ))}
                </div>
              </section>
            )}

            {/* 6 — Housekeeping queue */}
            <section>
              <SectionHeader
                title="งานทำความสะอาด"
                count={cleaningTasks.length > 0 ? cleaningTasks.length : needsCleaning.length}
              />
              <div className="mt-2.5 space-y-3">
                {cleaningTasks.length > 0 ? (
                  <>
                    {cleaningTasks.map(t => (
                      <CleaningRow key={t.id} t={t} checklist={checklistFor(t.id)} missingItems={missingItemsByTask.get(t.id) ?? []} index={next()} />
                    ))}
                    {cleaningTasks.some(t => t.requires_admin_attention) && (
                      <p className="inline-flex items-center gap-1 text-[12px] text-amber-600 py-1 pl-1">
                        <Sparkles size={12} className="flex-shrink-0" />
                        บางงานต้องให้แอดมินดู — สั่งงานได้ใน LINE
                      </p>
                    )}
                  </>
                ) : (
                  <>
                    {needsCleaning.map(b => (
                      <BookingRow key={b.id} b={b} onClick={() => onSelect(b)} index={next()} />
                    ))}
                    <p className="text-[12px] text-gray-400 py-1 pl-1">
                      {needsCleaning.length === 0
                        ? 'ยังไม่มีห้องค้างทำความสะอาด · ระบบคิวแม่บ้านยังไม่เชื่อมต่อ'
                        : 'แสดงจาก checkout ที่ยังไม่ได้ทำความสะอาด · ระบบคิวแม่บ้านยังไม่เชื่อมต่อ'}
                    </p>
                  </>
                )}
              </div>
            </section>

            {activeAccessPrepTasks.length > 0 && (
              <section>
                <SectionHeader title="งาน Access Prep" count={activeAccessPrepTasks.length} />
                <div className="mt-2.5 space-y-3">
                  {activeAccessPrepTasks.map(task => (
                    <AccessPrepRow
                      key={task.id}
                      task={task}
                      linkedCleaning={cleaningTasks.find(cleaning => cleaning.booking_id === task.booking_id)}
                      index={next()}
                    />
                  ))}
                </div>
              </section>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
