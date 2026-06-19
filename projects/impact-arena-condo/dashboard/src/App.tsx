import { useState } from 'react'
import { useDashboardData } from './hooks/useData'
import { BookingDetailPanel } from './components/BookingDetailPanel'
import { CaseDetailPanel } from './components/CaseDetailPanel'
import { BookingDraftPanel } from './components/BookingDraftPanel'
import { MessageDraftPanel } from './components/MessageDraftPanel'
import { TodayView } from './views/TodayView'
import { CalendarView } from './views/CalendarView'
import { RoomsView } from './views/RoomsView'
import { UpcomingView } from './views/UpcomingView'
import { RoomDetailPanel } from './components/RoomDetailPanel'
import type { TabView, Booking, Alert, BookingDraft, MessageDraft, Room, BookingAccessPreparation } from './lib/types'

const TOKEN = import.meta.env.VITE_DASHBOARD_TOKEN as string | undefined

const TABS: { id: TabView; label: string }[] = [
  { id: 'today', label: 'วันนี้' },
  { id: 'upcoming', label: 'กำลังจะเกิดขึ้น' },
  { id: 'calendar', label: 'ปฏิทิน' },
  { id: 'rooms', label: 'ห้อง' },
]


function TokenGate({ children }: { children: React.ReactNode }) {
  const hash = window.location.pathname.split('/').pop()
  if (TOKEN && hash !== TOKEN) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <p className="text-gray-400 text-sm">ไม่พบหน้านี้</p>
      </div>
    )
  }
  return <>{children}</>
}

export default function App() {
  const [tab, setTab] = useState<TabView>('today')
  const [selected, setSelected] = useState<Booking | null>(null)
  const [selectedCase, setSelectedCase] = useState<Alert | null>(null)
  const [selectedDraft, setSelectedDraft] = useState<BookingDraft | null>(null)
  const [selectedMsgDraft, setSelectedMsgDraft] = useState<MessageDraft | null>(null)
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null)
  const { bookings, rooms, roomStatuses, alerts, drafts, stayStates, holds, cleaningTasks, accessPrepTasks, checklistItems, bookingDrafts, conversations, outboundMessages, events, guestTags, guestNotes, accessPreps, loading, error, connected, lastUpdated, refresh } =
    useDashboardData()

  return (
    <TokenGate>
      <div className="min-h-screen bg-white font-sans">
        <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-[#EBEBEB]/80">
          <div className="max-w-7xl mx-auto px-4 md:px-8">
            {/* Logo row */}
            <div className="flex items-center justify-between pt-3 pb-1 md:pt-4 md:pb-2">
              <span className="font-bold text-[18px] md:text-[20px] tracking-tight text-[#222222] flex items-center gap-1.5">
                Impact Arena Condo
                <span className="w-1.5 h-1.5 rounded-full bg-[#FF385C]" />
              </span>
              <div className="flex items-center gap-2">
                {error ? (
                  <span className="text-[11px] text-[#FF385C] bg-red-50 px-2 py-0.5 rounded-full font-medium">
                    ข้อมูลขัดข้อง
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 text-[12px] font-medium">
                    <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-gray-300'}`} />
                    <span className={connected ? 'text-green-600' : 'text-gray-400'}>
                      {connected ? 'ออนไลน์' : 'ออฟไลน์'}
                    </span>
                  </span>
                )}
              </div>
            </div>

            {/* Tab nav — iOS Premium Segmented Control (Text-Only) */}
            <div className="flex justify-center pb-3 md:pb-4">
              <nav className="relative inline-flex p-1 bg-[#EEEEF0] rounded-full border border-black/[0.03] w-[320px] md:w-[440px]" role="tablist">
                {/* Sliding indicator (crisp white pill contained inside container) */}
                <div
                  className="absolute left-[4px] top-[4px] bottom-[4px] rounded-full bg-white border border-black/[0.04] shadow-[0_3px_8px_rgba(0,0,0,0.12),0_1px_3px_rgba(0,0,0,0.04)] pointer-events-none"
                  style={{
                    width: 'calc((100% - 8px) / 4)',
                    transform: `translateX(calc(${TABS.findIndex(t => t.id === tab)} * 100%))`,
                    transition: 'transform 320ms cubic-bezier(0.16, 1, 0.3, 1)',
                    willChange: 'transform',
                  }}
                />
                {TABS.map(({ id, label }) => {
                  const isActive = tab === id
                  return (
                    <button
                      key={id}
                      role="tab"
                      aria-selected={isActive}
                      onClick={() => setTab(id)}
                      className={`relative z-10 flex-1 py-1.5 md:py-2 text-[13px] md:text-[14px] font-semibold rounded-full text-center transition-all duration-200 focus-visible:outline-none active:scale-95 ${
                        isActive
                          ? 'text-[#222222]'
                          : 'text-[#717171] hover:text-[#222222]'
                      }`}
                    >
                      {id === 'upcoming' ? (
                        <>
                          <span className="hidden md:inline">กำลังจะเกิดขึ้น</span>
                          <span className="inline md:hidden">ล่วงหน้า</span>
                        </>
                      ) : (
                        label
                      )}
                    </button>
                  )
                })}
              </nav>
            </div>
          </div>
        </header>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="flex flex-col items-center gap-3">
              <div className="w-5 h-5 border-2 border-[#222222] border-t-transparent rounded-full animate-spin" />
              <span className="text-[13px] text-gray-400">กำลังโหลด...</span>
            </div>
          </div>
        ) : (
          <div key={tab} className="animate-fadeIn">
            {tab === 'today' && (
              <TodayView
                bookings={bookings}
                rooms={rooms}
                roomStatuses={roomStatuses}
                alerts={alerts}
                drafts={drafts}
                stayStates={stayStates}
                holds={holds}
                cleaningTasks={cleaningTasks}
                accessPrepTasks={accessPrepTasks}
                checklistItems={checklistItems}
                bookingDrafts={bookingDrafts}
                accessPreps={accessPreps}
                lastUpdated={lastUpdated}
                onSelect={setSelected}
                onSelectCase={setSelectedCase}
                onSelectDraft={setSelectedDraft}
                onSelectDraftMsg={setSelectedMsgDraft}
              />
            )}
            {tab === 'calendar' && (
              <div className="flex flex-col" style={{ height: 'calc(100dvh - 90px)' }}>
                <CalendarView
                  bookings={bookings}
                  rooms={rooms}
                  roomStatuses={roomStatuses}
                  holds={holds}
                  cleaningTasks={cleaningTasks}
                  events={events}
                  lastUpdated={lastUpdated}
                  onSelect={setSelected}
                />
              </div>
            )}
            {tab === 'rooms' && (
              <RoomsView
                rooms={rooms}
                roomStatuses={roomStatuses}
                bookings={bookings}
                holds={holds}
                cleaningTasks={cleaningTasks}
                lastUpdated={lastUpdated}
                onSelect={setSelected}
                onRefresh={refresh}
                onSelectRoom={setSelectedRoom}
              />
            )}
            {tab === 'upcoming' && (
              <UpcomingView
                bookings={bookings}
                rooms={rooms}
                holds={holds}
                cleaningTasks={cleaningTasks}
                lastUpdated={lastUpdated}
                onSelect={setSelected}
              />
            )}
          </div>
        )}

        {selectedCase && (
          <CaseDetailPanel
            alert={selectedCase}
            bookings={bookings}
            drafts={drafts}
            onClose={() => setSelectedCase(null)}
            onOpenBooking={(b) => { setSelectedCase(null); setSelected(b) }}
            onOpenDraft={(d) => { setSelectedCase(null); setSelectedMsgDraft(d) }}
          />
        )}

        {selectedDraft && (
          <BookingDraftPanel
            draft={selectedDraft}
            bookings={bookings}
            onClose={() => setSelectedDraft(null)}
            onOpenBooking={(b) => { setSelectedDraft(null); setSelected(b) }}
          />
        )}

        {selectedMsgDraft && (
          <MessageDraftPanel
            draft={selectedMsgDraft}
            conversations={conversations}
            outboundMessages={outboundMessages}
            bookings={bookings}
            onClose={() => setSelectedMsgDraft(null)}
            onOpenBooking={(b) => { setSelectedMsgDraft(null); setSelected(b) }}
          />
        )}

        {selected && (
          <BookingDetailPanel
            booking={selected}
            bookings={bookings}
            stayStates={stayStates}
            holds={holds}
            cleaningTasks={cleaningTasks}
            accessPrepTasks={accessPrepTasks}
            checklistItems={checklistItems}
            events={events}
            guestTags={guestTags}
            guestNotes={guestNotes}
            accessPreps={accessPreps}
            onClose={() => setSelected(null)}
          />
        )}

        {selectedRoom && (
          <RoomDetailPanel
            room={selectedRoom}
            roomStatuses={roomStatuses}
            bookings={bookings}
            onClose={() => setSelectedRoom(null)}
            onSelectBooking={(b) => {
              setSelectedRoom(null)
              setSelected(b)
            }}
            onCoverUpdated={() => {
              refresh()
            }}
          />
        )}
      </div>
    </TokenGate>
  )
}
