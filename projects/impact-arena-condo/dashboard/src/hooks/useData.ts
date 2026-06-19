import { useEffect, useState, useCallback } from 'react'
import { supabase } from '../lib/supabase'
import type {
  Booking, Room, RoomStatus, Alert, MessageDraft, GuestStayState, RoomAccessHold,
  CleaningTask, CleaningChecklistItem, BookingDraft, Conversation, OutboundMessage,
  EventCalendar, GuestTag, GuestNote, BookingAccessPreparation, AccessPrepTask,
} from '../lib/types'

export interface DashboardData {
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
  conversations: Conversation[]
  outboundMessages: OutboundMessage[]
  // D7
  events: EventCalendar[]
  guestTags: GuestTag[]
  guestNotes: GuestNote[]
  accessPreps: BookingAccessPreparation[]
  loading: boolean
  error: string | null
  lastUpdated: Date | null
  connected: boolean
  refresh: () => Promise<void>
}

// internal_ops_cases columns. case_code is in the v1 schema contract but may not be
// live in every environment yet, so it is selected separately with a graceful fallback.
const CASE_COLUMNS_BASE = `
  id, case_type, priority, status,
  room_code_snapshot, guest_display_snapshot, reservation_number_snapshot,
  issue_summary, ai_suggestion, admin_action_needed, booking_id, created_at
`

// Extra columns used only by the Case Detail panel (D2). All in the v1 schema contract
// but selected via fallback in case an environment hasn't migrated them yet.
const CASE_DETAIL_COLUMNS = `
  platform_snapshot, channel_target,
  check_in_date_snapshot, check_out_date_snapshot,
  latest_guest_message_excerpt, active_message_draft_id, assigned_admin_user_id
`

export function useDashboardData(): DashboardData {
  const [bookings, setBookings] = useState<Booking[]>([])
  const [rooms, setRooms] = useState<Room[]>([])
  const [roomStatuses, setRoomStatuses] = useState<RoomStatus[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [drafts, setDrafts] = useState<MessageDraft[]>([])
  const [stayStates, setStayStates] = useState<GuestStayState[]>([])
  const [holds, setHolds] = useState<RoomAccessHold[]>([])
  const [cleaningTasks, setCleaningTasks] = useState<CleaningTask[]>([])
  const [accessPrepTasks, setAccessPrepTasks] = useState<AccessPrepTask[]>([])
  const [checklistItems, setChecklistItems] = useState<CleaningChecklistItem[]>([])
  const [bookingDrafts, setBookingDrafts] = useState<BookingDraft[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [outboundMessages, setOutboundMessages] = useState<OutboundMessage[]>([])
  // D7
  const [events, setEvents] = useState<EventCalendar[]>([])
  const [guestTags, setGuestTags] = useState<GuestTag[]>([])
  const [guestNotes, setGuestNotes] = useState<GuestNote[]>([])
  const [accessPreps, setAccessPreps] = useState<BookingAccessPreparation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [connected, setConnected] = useState(false)

  const fetchAll = useCallback(async () => {
    try {
      const today = new Date()
      const windowStart = new Date(today)
      windowStart.setDate(today.getDate() - 1)
      const windowEnd = new Date(today)
      windowEnd.setDate(today.getDate() + 60)

      // Cases: progressive column fallback so a not-yet-migrated env still shows alerts.
      // Tier 1 = rich detail columns (D2), Tier 2 = base + case_code, Tier 3 = base only.
      const loadCases = async () => {
        const ordered = (sel: string) =>
          supabase
            .from('internal_ops_cases')
            .select(sel)
            .not('status', 'in', '("resolved","closed")')
            .order('priority', { ascending: false })
            .order('created_at', { ascending: false })
            .limit(50)
        const rich = await ordered(`case_code, ${CASE_DETAIL_COLUMNS}, ${CASE_COLUMNS_BASE}`)
        if (!rich.error) return rich.data ?? []
        const withCode = await ordered(`case_code, ${CASE_COLUMNS_BASE}`)
        if (!withCode.error) return withCode.data ?? []
        const base = await ordered(CASE_COLUMNS_BASE)
        if (base.error) throw base.error
        return (base.data ?? []).map((c: any) => ({ ...c, case_code: null }))
      }

      // Stay states power evidence language. Read-only and tolerant: if anon RLS blocks
      // this table, the dashboard still works — evidence just falls back to neutral wording.
      const loadStays = async (): Promise<GuestStayState[]> => {
        const res = await supabase
          .from('guest_stay_states')
          .select(
            'booking_id, check_in_signal_status, check_out_signal_status, room_access_package_status, booking_verification_status, journey_stage, updated_at',
          )
        return res.error ? [] : ((res.data ?? []) as GuestStayState[])
      }

      // Active room access holds (un-released). Tolerant: never breaks the dashboard.
      const loadHolds = async (): Promise<RoomAccessHold[]> => {
        const res = await supabase
          .from('room_access_holds')
          .select('id, booking_id, room_id, hold_type, hold_reason, hold_status, priority, created_at, released_at, last_recheck_result')
          .is('released_at', null)
        return res.error ? [] : ((res.data ?? []) as RoomAccessHold[])
      }

      // Open cleaning tasks (D4). Tolerant + join fallback: the table may not be migrated
      // yet (404) — in that case the housekeeping queue simply shows "ยังไม่เชื่อมต่อ".
      const CLEANING_COLS =
        'id, room_id, booking_id, task_type, priority, status, checklist_status, ' +
        'checkin_risk_level, requires_admin_attention, due_at, planned_start_at, ' +
        'room_ready_at, completed_at, instructions, blocker_reason, created_at, updated_at'
      const loadCleaningTasks = async (): Promise<CleaningTask[]> => {
        const flatten = (rows: any[]): CleaningTask[] =>
          rows.map(t => ({ ...t, room_code: t.rooms?.room_code ?? null, building: t.rooms?.building ?? null }))
        const withRooms = await supabase
          .from('cleaning_tasks')
          .select(`${CLEANING_COLS}, rooms!left(room_code, building)`)
          .is('completed_at', null)
          .order('due_at', { ascending: true })
        if (!withRooms.error) return flatten(withRooms.data ?? [])
        const bare = await supabase
          .from('cleaning_tasks')
          .select(CLEANING_COLS)
          .is('completed_at', null)
        return bare.error ? [] : flatten(bare.data ?? [])
      }

      const loadAccessPrepTasks = async (): Promise<AccessPrepTask[]> => {
        const cols =
          'id, booking_id, room_id, priority, status, key_custody, due_at, scheduled_for, ' +
          'blocker_reason, assigned_housekeeper_id, owner_admin_user_id, override_reason, overridden_at'
        const flatten = (rows: any[]): AccessPrepTask[] =>
          rows.map(t => ({ ...t, room_code: t.rooms?.room_code ?? null, building: t.rooms?.building ?? null }))
        const withRooms = await supabase
          .from('access_prep_tasks')
          .select(`${cols}, rooms!left(room_code, building)`)
          .not('status', 'in', '("done","canceled")')
          .order('due_at', { ascending: true })
        if (!withRooms.error) {
          const active = flatten(withRooms.data ?? [])
          const overridden = await supabase
            .from('access_prep_tasks')
            .select(`${cols}, rooms!left(room_code, building)`)
            .not('overridden_at', 'is', null)
            .order('overridden_at', { ascending: false })
            .limit(30)
          const combined = [...active, ...flatten(overridden.error ? [] : overridden.data ?? [])]
          return [...new Map(combined.map(task => [task.id, task])).values()]
        }
        const bare = await supabase
          .from('access_prep_tasks')
          .select(cols)
          .not('status', 'in', '("done","canceled")')
        if (bare.error) return []
        const overridden = await supabase
          .from('access_prep_tasks')
          .select(cols)
          .not('overridden_at', 'is', null)
          .order('overridden_at', { ascending: false })
          .limit(30)
        const combined = [...flatten(bare.data ?? []), ...flatten(overridden.error ? [] : overridden.data ?? [])]
        return [...new Map(combined.map(task => [task.id, task])).values()]
      }

      // Checklist items for the open tasks. Tolerant; grouped by cleaning_task_id in the UI.
      const loadChecklistItems = async (): Promise<CleaningChecklistItem[]> => {
        const res = await supabase
          .from('cleaning_task_checklist_items')
          .select('id, cleaning_task_id, room_id, item_key, item_label, required, status, issue_note, exception_reason')
        return res.error ? [] : ((res.data ?? []) as CleaningChecklistItem[])
      }

      // Booking evidence drafts (D5) — screenshots/OCR awaiting admin review. Pending first,
      // then recently-actioned for context. Tolerant: never breaks the dashboard.
      const loadBookingDrafts = async (): Promise<BookingDraft[]> => {
        const res = await supabase
          .from('booking_drafts')
          .select('id, session_id, source_type, platform, raw_input_ref, extracted_json, extraction_confidence, status, admin_notes, approved_booking_id, created_at, updated_at')
          .order('created_at', { ascending: false })
          .limit(40)
        return res.error ? [] : ((res.data ?? []) as BookingDraft[])
      }

      // Conversation takeover/automation state (D6) — bot active vs admin-paused. Tolerant.
      const loadConversations = async (): Promise<Conversation[]> => {
        const res = await supabase
          .from('conversations')
          .select('id, booking_id, channel, status, automation_mode, bot_paused_at, bot_pause_reason, handoff_state, risk_level, latest_intent')
        return res.error ? [] : ((res.data ?? []) as Conversation[])
      }

      // Outbound send evidence (D6) — proof a draft actually went out. Tolerant; linked by
      // message_draft_id in the draft panel.
      const loadOutbound = async (): Promise<OutboundMessage[]> => {
        const res = await supabase
          .from('outbound_messages')
          .select('id, message_draft_id, booking_id, target_channel, send_status, approval_status, sent_at, delivered_at, error, created_at')
          .order('created_at', { ascending: false })
          .limit(100)
        return res.error ? [] : ((res.data ?? []) as OutboundMessage[])
      }

      // ── D7: Event Calendar + Guest Tags + Guest Notes (tolerant — all 404 until migrated) ──

      // Published events only — draft/pending never surfaced (product rule).
      const loadEvents = async (): Promise<EventCalendar[]> => {
        const res = await supabase
          .from('event_calendar')
          .select('id, event_name, event_type, venue, start_date, end_date, status, soft_question_template, visitor_hint, notes, created_at')
          .eq('status', 'published')
          .order('start_date', { ascending: true })
        return res.error ? [] : ((res.data ?? []) as EventCalendar[])
      }

      // Guest context tags — repeat interest / visitor type signals per booking.
      const loadGuestTags = async (): Promise<GuestTag[]> => {
        const res = await supabase
          .from('guest_tags')
          .select('id, booking_id, tag_key, tag_label, source, created_at')
          .order('created_at', { ascending: false })
        return res.error ? [] : ((res.data ?? []) as GuestTag[])
      }

      // Admin context notes per booking.
      const loadGuestNotes = async (): Promise<GuestNote[]> => {
        const res = await supabase
          .from('guest_notes')
          .select('id, booking_id, note_text, note_type, created_by, created_at')
          .order('created_at', { ascending: false })
        return res.error ? [] : ((res.data ?? []) as GuestNote[])
      }

      const loadAccessPreps = async (): Promise<BookingAccessPreparation[]> => {
        const res = await supabase
          .from('booking_access_preparations')
          .select('id, booking_id, room_id, key_placed_in_room, key_placed_at, key_placed_by, room_left_unlocked_or_open, room_opened_at, room_opened_by, note, status, created_at, updated_at')
        return res.error ? [] : ((res.data ?? []) as BookingAccessPreparation[])
      }

      const [bookingsRes, roomsRes, roomStatusRes, alertRows, draftsRes, stayRows, holdRows, cleaningRows, accessPrepTaskRows, checklistRows, bookingDraftRows, conversationRows, outboundRows, eventRows, tagRows, noteRows, accessPrepRows] = await Promise.all([
        supabase
          .from('bookings')
          .select(`
            id, platform, reservation_number, guest_name_snapshot,
            check_in_date, check_out_date, nights, room_id,
            booking_status, booking_status_updated_at, created_at, updated_at,
            rooms!left(room_code, building, portfolio, photo_url, room_status!left(cleaning_status, occupancy_status))
          `)
          .not('booking_status', 'in', '("cancelled","no_show","draft")')
          .gte('check_out_date', windowStart.toISOString().slice(0, 10))
          .lte('check_in_date', windowEnd.toISOString().slice(0, 10))
          .order('check_in_date', { ascending: true }),

        supabase
          .from('rooms')
          .select('id, room_code, building, floor, room_number, portfolio, listing_tier, quality_tier, active, photo_url')
          .eq('active', true)
          .order('building'),

        supabase
          .from('room_status')
          .select('room_id, cleaning_status, occupancy_status, maintenance_status, last_cleaned_at, updated_at'),

        loadCases(),

        supabase
          .from('message_drafts')
          .select(`
            id, booking_id, conversation_id, internal_ops_case_id, status, draft_purpose,
            room_code_snapshot, guest_display_snapshot, platform_snapshot, reservation_number_snapshot,
            channel_target, delivery_mode, draft_text, approval_required, auto_send_allowed,
            draft_importance, draft_trigger, reason, visible_context_summary, evidence_summary,
            latest_guest_message_excerpt, admin_action_needed, approved_by, approved_at, created_at
          `)
          .eq('status', 'draft')
          .order('created_at', { ascending: false })
          .limit(20),

        loadStays(),
        loadHolds(),
        loadCleaningTasks(),
        loadAccessPrepTasks(),
        loadChecklistItems(),
        loadBookingDrafts(),
        loadConversations(),
        loadOutbound(),
        loadEvents(),
        loadGuestTags(),
        loadGuestNotes(),
        loadAccessPreps(),
      ])

      if (bookingsRes.error) throw bookingsRes.error
      if (roomsRes.error) throw roomsRes.error
      if (roomStatusRes.error) throw roomStatusRes.error
      if (draftsRes.error) throw draftsRes.error

      const flatBookings: Booking[] = (bookingsRes.data ?? []).map((b: any) => ({
        ...b,
        room_code: b.rooms?.room_code ?? null,
        building: b.rooms?.building ?? null,
        portfolio: b.rooms?.portfolio ?? null,
        cleaning_status: b.rooms?.room_status?.cleaning_status ?? null,
        occupancy_status: b.rooms?.room_status?.occupancy_status ?? null,
        photo_url: b.rooms?.photo_url ?? null,
      }))

      setBookings(flatBookings)
      setRooms(roomsRes.data ?? [])
      setRoomStatuses(roomStatusRes.data ?? [])
      setAlerts(alertRows as Alert[])
      setDrafts(draftsRes.data ?? [])
      setStayStates(stayRows)
      setHolds(holdRows)
      setCleaningTasks(cleaningRows)
      setAccessPrepTasks(accessPrepTaskRows)
      setChecklistItems(checklistRows)
      setBookingDrafts(bookingDraftRows)
      setConversations(conversationRows)
      setOutboundMessages(outboundRows)
      setEvents(eventRows)
      setGuestTags(tagRows)
      setGuestNotes(noteRows)
      setAccessPreps(accessPrepRows)
      setError(null)
      setLastUpdated(new Date())
    } catch (err: any) {
      setError(err?.message ?? 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()

    const channel = supabase
      .channel('dashboard-realtime')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'bookings' }, fetchAll)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'rooms' }, fetchAll)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'room_status' }, fetchAll)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'internal_ops_cases' }, fetchAll)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'message_drafts' }, fetchAll)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'guest_stay_states' }, fetchAll)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'room_access_holds' }, fetchAll)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'cleaning_tasks' }, fetchAll)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'access_prep_tasks' }, fetchAll)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'cleaning_task_checklist_items' }, fetchAll)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'booking_drafts' }, fetchAll)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'conversations' }, fetchAll)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'outbound_messages' }, fetchAll)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'event_calendar' }, fetchAll)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'guest_tags' }, fetchAll)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'guest_notes' }, fetchAll)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'booking_access_preparations' }, fetchAll)
      .subscribe((status) => {
        setConnected(status === 'SUBSCRIBED')
      })

    return () => { supabase.removeChannel(channel) }
  }, [fetchAll])

  return { bookings, rooms, roomStatuses, alerts, drafts, stayStates, holds, cleaningTasks, accessPrepTasks, checklistItems, bookingDrafts, conversations, outboundMessages, events, guestTags, guestNotes, accessPreps, loading, error, lastUpdated, connected, refresh: fetchAll }
}
