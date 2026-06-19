import { useEffect, useState } from 'react'
import { parseISO } from 'date-fns'
import { X, Globe, Hash, CheckCircle2, Circle, ShieldCheck, ShieldAlert, KeyRound, BadgeCheck, Send, Sparkles, Clock, CalendarDays, Tag, StickyNote } from 'lucide-react'
import type { Booking, GuestStayState, RoomAccessHold, CleaningTask, CleaningChecklistItem, EventCalendar, GuestTag, GuestNote, BookingAccessPreparation, AccessPrepTask } from '../lib/types'
import {
  thaiDate, getStatusColor, STATUS_LABEL,
  roomAccessVerdict, verificationLabel, packageStatusLabel, HOLD_REASON_LABEL,
  cleaningTaskStatusLabel, checklistItemLabel, dueLabel,
  overlappingEvents, eventTypeLabel, guestTagLabel,
  accessPrepTaskStatusLabel, ownerOverrideWarning,
} from '../lib/types'
import { StatusDot } from './StatusDot'
import { PlatformPill } from './PlatformPill'
import { RoomMiniCalendar } from './RoomMiniCalendar'

interface Props {
  booking: Booking | null
  bookings: Booking[]
  stayStates: GuestStayState[]
  holds: RoomAccessHold[]
  cleaningTasks: CleaningTask[]
  accessPrepTasks: AccessPrepTask[]
  checklistItems: CleaningChecklistItem[]
  events: EventCalendar[]
  guestTags: GuestTag[]
  guestNotes: GuestNote[]
  accessPreps: BookingAccessPreparation[]
  onClose: () => void
}

function statusText(b: Booking, color: string): string {
  if (b.booking_status === 'cancelled') return 'ยกเลิก'
  if (b.booking_status === 'no_show')   return 'ไม่มาเข้าพัก'
  if (b.booking_status === 'draft')     return 'ฉบับร่าง'
  return STATUS_LABEL[color] ?? '—'
}

const cleaningLabel: Record<string, string> = {
  clean:                'สะอาดแล้ว',
  dirty:                'รอทำความสะอาด',
  cleaning_in_progress: 'กำลังทำความสะอาด',
  unknown:              'ไม่ทราบ',
}

function Row({ icon, label, value }: { icon: React.ReactNode; label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-3.5 border-b border-[#F5F5F5] last:border-0">
      <div className="flex items-center gap-2.5 min-w-0">
        <span className="text-gray-400 flex-shrink-0">
          {icon}
        </span>
        <span className="text-[13.5px] font-medium text-gray-500">{label}</span>
      </div>
      <div className="text-[14px] text-[#222222] font-semibold truncate ml-3">{value || '—'}</div>
    </div>
  )
}

export function BookingDetailPanel({ booking, bookings, stayStates, holds, cleaningTasks, accessPrepTasks, checklistItems, events, guestTags, guestNotes, accessPreps, onClose }: Props) {
  const [closing, setClosing] = useState(false)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { setClosing(true); setTimeout(onClose, 230) }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  if (!booking) return null

  const statusColor = getStatusColor(booking.booking_status, booking.cleaning_status)

  const stay = stayStates.find(s => s.booking_id === booking.id)
  const hold = holds.find(h => h.booking_id === booking.id)
  const showAccess = booking.booking_status === 'confirmed' || booking.booking_status === 'checked_in'
  const accessPrep = accessPreps.find(ap => ap.booking_id === booking.id)
  const verdict = roomAccessVerdict(booking, stay, hold, accessPrep)

  const task = cleaningTasks.find(t => t.booking_id === booking.id)
    ?? cleaningTasks.find(t => t.room_id === booking.room_id)
  const taskChecklist = task ? checklistItems.filter(it => it.cleaning_task_id === task.id) : []
  const taskDue = task ? dueLabel(task.due_at) : null
  const accessPrepTask = accessPrepTasks.find(t => t.booking_id === booking.id)
  const linkedCleaning = accessPrepTask
    ? cleaningTasks.find(t => t.booking_id === accessPrepTask.booking_id)
    : undefined
  const accessPrepOverrideWarning = accessPrepTask ? ownerOverrideWarning(accessPrepTask) : null

  const bookingEvents = overlappingEvents(booking, events)
  const bookingTags   = guestTags.filter(t => t.booking_id === booking.id)
  const bookingNotes  = guestNotes.filter(n => n.booking_id === booking.id)
  const showHumanCare = bookingEvents.length > 0 || bookingTags.length > 0 || bookingNotes.length > 0

  const handleClose = () => {
    setClosing(true)
    setTimeout(onClose, 230)
  }

  const guestInitial = booking.guest_name_snapshot ? booking.guest_name_snapshot.trim().charAt(0) : 'G'

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/20 z-40 ${closing ? 'animate-fadeOut' : 'animate-fadeBackdrop'}`}
        onClick={handleClose}
      />

      {/* Panel */}
      <div className={`fixed bottom-0 left-0 right-0 md:right-4 md:top-4 md:bottom-4 md:left-auto md:w-[420px] bg-white rounded-t-[32px] md:rounded-[24px] z-50 flex flex-col min-h-[75vh] max-h-[95vh] md:min-h-0 md:max-h-none md:h-[calc(100vh-32px)] shadow-[0_-8px_32px_rgba(0,0,0,0.06)] md:shadow-[0_8px_32px_rgba(0,0,0,0.08)] md:border md:border-[#EBEBEB]/80 ${closing ? 'animate-slideDown md:animate-slideOutRight' : 'animate-slideUp md:animate-slideInRight'}`}>

        {/* Drag handle for mobile */}
        <div className="flex justify-center pt-3 pb-2 md:hidden flex-shrink-0">
          <div className="w-10 h-1.5 rounded-full bg-[#EBEBEB]" />
        </div>

        {/* Header — Guest profile avatar, name and room code */}
        <div className="px-6 pt-3 pb-5 border-b border-[#F5F5F5] flex-shrink-0">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-3.5 min-w-0">
              {/* Profile Avatar */}
              <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-[#FF385C] to-[#E61E43] flex items-center justify-center text-white font-bold text-[18px] shadow-sm flex-shrink-0">
                {guestInitial}
              </div>
              <div className="min-w-0">
                <h2 className="text-[20px] font-bold text-[#222222] truncate leading-tight">
                  {booking.guest_name_snapshot}
                </h2>
                <p className="text-[13px] text-gray-500 mt-1 flex items-center gap-1.5">
                  <span className="font-semibold text-[#222222]">{booking.room_code ?? '—'}</span>
                  <span>·</span>
                  <span className="inline-flex items-center gap-1">
                    <StatusDot color={statusColor as any} size="sm" />
                    {statusText(booking, statusColor)}
                  </span>
                </p>
              </div>
            </div>
            {/* Close Button */}
            <button
              onClick={handleClose}
              className="w-9 h-9 rounded-full bg-[#F7F7F7] border border-[#EBEBEB] flex items-center justify-center flex-shrink-0 active:scale-90 transition shadow-sm hover:bg-gray-100"
              aria-label="ปิด"
            >
              <X size={15} className="text-[#222222]" />
            </button>
          </div>
        </div>

        {/* Scrollable content */}
        <div className="overflow-y-auto flex-1 px-6 pt-5">

          {/* Stay duration — Ticket layout */}
          <div
            className="animate-riseIn bg-[#F7F7F7] border border-[#EBEBEB] rounded-[24px] p-4 flex items-center justify-between"
            style={{ ['--i' as string]: 0 } as React.CSSProperties}
          >
            <div className="flex-1">
              <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">เช็กอิน</span>
              <p className="text-[17px] font-extrabold text-[#222222] mt-0.5 leading-tight">
                {thaiDate(booking.check_in_date)}
              </p>
              <span className="text-[11px] text-gray-400 mt-1 block">14:00 น. เป็นต้นไป</span>
            </div>

            <div className="flex flex-col items-center px-3 flex-shrink-0">
              <span className="text-[11px] font-bold text-[#FF385C] bg-white border border-[#FF385C]/15 rounded-full px-3 py-1 shadow-sm whitespace-nowrap">
                {booking.nights} คืน
              </span>
              <div className="h-[2px] w-8 bg-[#EBEBEB] mt-2" />
            </div>

            <div className="flex-1 text-right">
              <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">เช็กเอาต์</span>
              <p className="text-[17px] font-extrabold text-[#222222] mt-0.5 leading-tight">
                {thaiDate(booking.check_out_date)}
              </p>
              <span className="text-[11px] text-gray-400 mt-1 block">ก่อน 11:00 น.</span>
            </div>
          </div>

          {/* Booking detail — grouped soft card */}
          <div
            className="animate-riseIn bg-white border border-[#EBEBEB] rounded-[24px] px-4 mt-3 shadow-sm"
            style={{ ['--i' as string]: 1 } as React.CSSProperties}
          >
            <Row
              icon={<Globe size={15} />}
              label="แพลตฟอร์ม"
              value={<PlatformPill platform={booking.platform} size="sm" />}
            />
            {booking.reservation_number && (
              <Row
                icon={<Hash size={15} />}
                label="หมายเลขจอง"
                value={booking.reservation_number}
              />
            )}
            <Row
              icon={<CheckCircle2 size={15} />}
              label="ทำความสะอาด"
              value={
                <span className="inline-flex items-center gap-1.5">
                  <StatusDot
                    color={
                      booking.cleaning_status === 'clean' ? 'occupied'
                      : (booking.cleaning_status === 'dirty' || booking.cleaning_status === 'cleaning_in_progress') ? 'cleaning'
                      : 'vacant'
                    }
                  />
                  {cleaningLabel[booking.cleaning_status ?? 'unknown']}
                </span>
              }
            />
          </div>

          {/* Room access readiness — host checklist guidance */}
          {showAccess && (
            <div className="animate-riseIn mt-4" style={{ ['--i' as string]: 2 } as React.CSSProperties}>
              <p className="text-[13px] font-bold text-gray-400 mb-2 tracking-wide uppercase">คู่มือการเข้าห้อง</p>

              {/* Verdict banner - Host friendly peach/amber box */}
              <div
                className={`flex items-start gap-3 rounded-[24px] p-4 ${
                  verdict.level === 'blocked'
                    ? 'bg-[#FFF8F6] border border-[#FFE7E0]'
                    : verdict.level === 'safe'
                    ? 'bg-[#F4FAF5] border border-[#E1F2E5]'
                    : 'bg-[#FFFBF0] border border-[#FEEFC3]'
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  verdict.level === 'blocked'
                    ? 'bg-[#FFE7E0] text-[#FF385C]'
                    : verdict.level === 'safe'
                    ? 'bg-[#E1F2E5] text-green-600'
                    : 'bg-[#FEEFC3] text-[#B06000]'
                }`}>
                  {verdict.level === 'blocked' ? <ShieldAlert size={16} /> : <ShieldCheck size={16} />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-[14px] font-bold ${
                    verdict.level === 'blocked'
                      ? 'text-[#C5221F]'
                      : verdict.level === 'safe'
                      ? 'text-green-700'
                      : 'text-[#B06000]'
                  }`}>
                    {verdict.headline}
                  </p>
                  <div className="mt-2 space-y-1">
                    {verdict.reasons.map((r, i) => (
                      <p key={i} className="text-[12px] text-gray-500 flex items-center gap-1.5 leading-snug">
                        <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                          verdict.level === 'blocked'
                            ? 'bg-[#FF385C]'
                            : verdict.level === 'safe'
                            ? 'bg-green-500'
                            : 'bg-amber-500'
                        }`} />
                        {r}
                      </p>
                    ))}
                  </div>
                </div>
              </div>

              {/* Signals Checklist */}
              <div className="bg-white border border-[#EBEBEB] rounded-[24px] px-4 mt-2.5 shadow-sm">
                <Row
                  icon={<BadgeCheck size={15} />}
                  label="ยืนยันการจอง"
                  value={
                    <span className={stay?.booking_verification_status === 'verified' ? 'text-green-600 font-semibold' : 'text-amber-600 font-semibold'}>
                      {verificationLabel(stay?.booking_verification_status)}
                    </span>
                  }
                />
                <Row
                  icon={<CheckCircle2 size={15} />}
                  label="ความพร้อมห้อง"
                  value={
                    <span className={booking.cleaning_status === 'clean' ? 'text-green-600 font-semibold flex items-center gap-1.5' : 'text-amber-600 font-semibold flex items-center gap-1.5'}>
                      <StatusDot color={booking.cleaning_status === 'clean' ? 'occupied' : 'cleaning'} />
                      {cleaningLabel[booking.cleaning_status ?? 'unknown']}
                    </span>
                  }
                />
                <Row
                  icon={<ShieldAlert size={15} />}
                  label="Room Access Hold"
                  value={
                    <span className={hold ? 'text-red-500 font-semibold' : 'text-gray-400'}>
                      {hold ? (hold.hold_reason && HOLD_REASON_LABEL[hold.hold_reason] ? HOLD_REASON_LABEL[hold.hold_reason] : 'ติด Hold') : 'ไม่มี'}
                    </span>
                  }
                />
                <Row
                  icon={<Send size={15} />}
                  label="ส่งข้อมูลเข้าห้อง"
                  value={
                    <span className={stay?.room_access_package_status === 'sent' ? 'text-green-600 font-semibold' : 'text-gray-400'}>
                      {packageStatusLabel(stay?.room_access_package_status)}
                    </span>
                  }
                />
                <Row
                  icon={<KeyRound size={15} />}
                  label="Access Prep"
                  value={
                    accessPrep ? (
                      <span className="inline-flex flex-col items-end text-[13px]">
                        <span className={accessPrep.status === 'complete' ? 'text-green-600 font-semibold' : accessPrep.status === 'blocked' ? 'text-red-500 font-semibold' : 'text-amber-600 font-semibold'}>
                          {accessPrep.status === 'complete' ? 'เรียบร้อย' : accessPrep.status === 'blocked' ? 'ติดปัญหา' : accessPrep.status === 'partial' ? 'บางส่วน' : 'ยังไม่เริ่ม'}
                        </span>
                        <span className="text-[11px] text-gray-400 font-normal mt-0.5">
                          {accessPrep.key_placed_in_room ? 'วางกุญแจแล้ว' : 'ยังไม่วางกุญแจ'} · {accessPrep.room_left_unlocked_or_open ? 'เปิดห้องแล้ว' : 'ยังไม่เปิดห้อง'}
                        </span>
                      </span>
                    ) : (
                      <span className="text-gray-400 font-medium">ยังไม่มีข้อมูล</span>
                    )
                  }
                />
              </div>
            </div>
          )}

          {/* Housekeeping (D4) */}
          <div className="animate-riseIn mt-4" style={{ ['--i' as string]: 3 } as React.CSSProperties}>
            <p className="text-[13px] font-bold text-gray-400 mb-2 tracking-wide uppercase">งานทำความสะอาด</p>
            {task ? (
              <div className="bg-white border border-[#EBEBEB] rounded-[24px] px-4 py-1 shadow-sm">
                <Row icon={<Sparkles size={15} />} label="สถานะงาน" value={cleaningTaskStatusLabel(task.status)} />
                {taskDue && (
                  <Row
                    icon={<Clock size={15} />}
                    label="กำหนดเสร็จ"
                    value={<span className={taskDue === 'เลยกำหนดแล้ว' ? 'text-red-600 font-semibold' : ''}>{taskDue}</span>}
                  />
                )}
                {taskChecklist.length > 0 && (
                  <div className="py-3.5 border-b border-[#F5F5F5] last:border-0">
                    <p className="text-[13.5px] font-medium text-gray-500 mb-2">เช็กลิสต์</p>
                    <ul className="space-y-1.5">
                      {taskChecklist.map(it => {
                        const done = it.status === 'present' || it.status === 'done' || it.status === 'completed' || it.status === 'ok'
                        return (
                          <li key={it.id} className="flex items-center gap-2 text-[13.5px]">
                            {done
                              ? <CheckCircle2 size={14} className="text-green-500 flex-shrink-0" />
                              : <Circle size={14} className="text-gray-300 flex-shrink-0" />}
                            <span className={done ? 'text-[#222222] font-medium' : 'text-gray-500'}>{checklistItemLabel(it)}</span>
                            {it.issue_note && <span className="text-[12px] text-red-500">· {it.issue_note}</span>}
                          </li>
                        )
                      })}
                    </ul>
                  </div>
                )}
                {task.blocker_reason && (
                  <Row icon={<ShieldAlert size={15} />} label="ติดปัญหา" value={<span className="text-red-600 font-semibold">{task.blocker_reason}</span>} />
                )}
                {task.instructions && (
                  <div className="py-3.5">
                    <p className="text-[13.5px] font-medium text-gray-500 mb-1">หมายเหตุ</p>
                    <p className="text-[13.5px] text-[#222222] whitespace-pre-line leading-snug font-medium">{task.instructions}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white border border-[#EBEBEB] rounded-[24px] px-4 py-4 shadow-sm">
                <p className="text-[13px] text-gray-400 leading-snug">
                  ยังไม่มีงานทำความสะอาดในระบบ · ระบบคิวแม่บ้านยังไม่เชื่อมต่อ
                </p>
              </div>
            )}
          </div>

          <div className="animate-riseIn mt-4" style={{ ['--i' as string]: 4 } as React.CSSProperties}>
            <p className="text-[13px] font-bold text-gray-400 mb-2 tracking-wide uppercase">งาน Access Prep</p>
            {accessPrepTask ? (
              <div className="bg-white border border-[#EBEBEB] rounded-[24px] px-4 py-1 shadow-sm">
                <Row icon={<KeyRound size={15} />} label="สถานะงาน" value={accessPrepTaskStatusLabel(accessPrepTask.status)} />
                <Row
                  icon={<Sparkles size={15} />}
                  label="Cleaning ที่เชื่อม"
                  value={linkedCleaning ? cleaningTaskStatusLabel(linkedCleaning.status) : 'ยังไม่มีงานเชื่อมกัน'}
                />
                <Row
                  icon={<KeyRound size={15} />}
                  label="กุญแจ"
                  value={accessPrepTask.key_custody === 'placed_in_room' ? 'วางในห้องแล้ว' : accessPrepTask.key_custody === 'with_owner' ? 'อยู่กับเจ้าของ' : accessPrepTask.key_custody === 'with_operator' ? 'อยู่กับผู้ปฏิบัติงาน' : 'ยังไม่ระบุ'}
                />
                {accessPrepTask.blocker_reason && (
                  <Row icon={<ShieldAlert size={15} />} label="ติดปัญหา" value={<span className="text-red-600">{accessPrepTask.blocker_reason}</span>} />
                )}
                {accessPrepOverrideWarning && (
                  <div className="py-3.5 text-[12px] font-medium text-amber-700 flex items-start gap-2">
                    <ShieldAlert size={14} className="flex-shrink-0 mt-0.5" />
                    <span>{accessPrepOverrideWarning}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white border border-[#EBEBEB] rounded-[24px] px-4 py-4 shadow-sm">
                <p className="text-[13px] text-gray-400">ยังไม่มีงาน Access Prep สำหรับการจองนี้</p>
              </div>
            )}
          </div>

          {/* D7 — Human Care Context */}
          {showHumanCare && (
            <div className="animate-riseIn mt-4" style={{ ['--i' as string]: 4 } as React.CSSProperties}>
              <p className="text-[13px] font-bold text-gray-400 mb-2 tracking-wide uppercase">บริบทแขก & อีเวนต์</p>

              {/* Event overlap */}
              {bookingEvents.length > 0 && (
                <div className="space-y-2 mb-2.5">
                  {bookingEvents.map(ev => (
                    <div key={ev.id} className="bg-[#F4F8FD] border border-[#E1F0FA] rounded-[24px] p-4 shadow-sm">
                      <div className="flex items-center gap-2 mb-1.5">
                        <CalendarDays size={14} className="text-[#1A73E8] flex-shrink-0" />
                        <span className="text-[12px] font-bold text-[#1A73E8] uppercase tracking-wide">
                          {eventTypeLabel(ev.event_type)}
                        </span>
                        {ev.venue && (
                          <span className="text-[10px] text-[#1A73E8] bg-[#E8F0FE] rounded-full px-2 py-0.5 flex-shrink-0 font-semibold">
                            {ev.venue}
                          </span>
                        )}
                      </div>
                      <p className="text-[14px] font-bold text-[#1A73E8] leading-tight">
                        {ev.event_name ?? eventTypeLabel(ev.event_type)}
                      </p>
                      {ev.start_date && ev.end_date && (
                        <p className="text-[12px] text-gray-500 mt-1 font-medium">
                          {thaiDate(ev.start_date)} – {thaiDate(ev.end_date)}
                        </p>
                      )}
                      {ev.soft_question_template && (
                        <p className="text-[12px] text-gray-500 mt-1.5 italic leading-snug font-medium border-l-2 border-[#D2E3FC] pl-2">
                          "{ev.soft_question_template}"
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Guest tags */}
              {bookingTags.length > 0 && (
                <div className="bg-white border border-[#EBEBEB] rounded-[24px] px-4 py-3 mb-2.5 shadow-sm">
                  <p className="flex items-center gap-1.5 text-[12.5px] font-bold text-gray-400 mb-2.5 uppercase tracking-wide">
                    <Tag size={13} /> แท็กบริบทแขก
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {bookingTags.map(t => (
                      <span
                        key={t.id}
                        className="text-[12px] font-semibold text-gray-600 bg-[#F5F5F5] border border-[#EBEBEB] rounded-full px-3 py-1"
                      >
                        {guestTagLabel(t)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Admin notes */}
              {bookingNotes.length > 0 && (
                <div className="bg-[#FFFDF6] border border-[#FEF5D1] rounded-[24px] p-4 shadow-sm">
                  <p className="flex items-center gap-1.5 text-[12.5px] font-bold text-[#B06000] mb-2.5 uppercase tracking-wide">
                    <StickyNote size={13} /> บันทึกแอดมิน
                  </p>
                  <div className="space-y-2">
                    {bookingNotes.map(n => (
                      <p key={n.id} className="text-[13.5px] text-[#222222] leading-snug whitespace-pre-line font-medium">
                        {n.note_text}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Room availability mini calendar */}
          <div className="animate-riseIn pt-6 pb-6 pb-safe" style={{ ['--i' as string]: 5 } as React.CSSProperties}>
            <p className="text-[13px] font-bold text-gray-400 mb-2.5 tracking-wide uppercase">ปฏิทินห้องนี้</p>
            <RoomMiniCalendar
              roomId={booking.room_id}
              bookings={bookings}
              currentBookingId={booking.id}
              initialMonth={parseISO(booking.check_in_date)}
            />
          </div>
        </div>

      </div>
    </>
  )
}
