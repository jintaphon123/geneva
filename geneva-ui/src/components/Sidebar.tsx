import { type ReactNode, useEffect, useMemo, useRef, useState } from "react"
import {
  AlertCircle,
  Archive,
  Box,
  FolderOpen,
  MessageCircle,
  MessageSquare,
  PanelLeftClose,
  Plus,
  Pencil,
  Pin,
  PinOff,
  RefreshCw,
  MoreVertical,
  Trash2,
  Search,
  Settings2,
  Sparkle,
} from "lucide-react"
import { GenevaMark } from "@/components/GenevaMark"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import type { MemoryStats, Project, SessionSummary } from "@/types"

type SidebarTab = "chat" | "skill"
const INITIAL_PROJECT_LIMIT = 5
const PROJECT_PAGE_SIZE = 12
const INITIAL_SESSION_LIMIT = 30

type SidebarProps = {
  sessions: SessionSummary[]
  activeSessionId: string | null
  memoryStats: MemoryStats
  activeTab: SidebarTab
  collapsed: boolean
  projects: Project[]
  projectsLoading?: boolean
  projectsError?: string | null
  activeProjectId: string | null
  onNewChat: () => void
  onOpenSearch: () => void
  onOpenSource: () => void
  onOpenArtifacts: () => void
  onOpenSettings: () => void
  onSelectProject: (project: Project) => void
  onOpenProjectChat: (project: Project) => void
  onCreateProject: () => void
  onRetryProjects?: () => void
  onSelectSession: (sessionId: string) => void
  onDeleteSession: (sessionId: string) => void
  onPinSession: (sessionId: string) => void
  onRenameSession: (sessionId: string, newTitle: string) => Promise<void>
  onAddToProject?: (sessionId: string) => void
  onTabChange: (tab: SidebarTab) => void
  onToggleCollapsed: () => void
}

export function Sidebar({
  sessions,
  activeSessionId,
  memoryStats,
  activeTab,
  collapsed,
  projects,
  projectsLoading = false,
  projectsError = null,
  activeProjectId,
  onNewChat,
  onOpenSearch,
  onOpenSource,
  onOpenArtifacts,
  onOpenSettings,
  onSelectProject,
  onOpenProjectChat,
  onCreateProject,
  onRetryProjects,
  onSelectSession,
  onDeleteSession,
  onPinSession,
  onRenameSession,
  onAddToProject,
  onTabChange,
  onToggleCollapsed,
}: SidebarProps) {
  const [projectLimit, setProjectLimit] = useState(INITIAL_PROJECT_LIMIT)
  const [sessionLimit, setSessionLimit] = useState(INITIAL_SESSION_LIMIT)
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)
  const [hoveredSessionId, setHoveredSessionId] = useState<string | null>(null)
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState("")
  const menuRef = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const visibleProjectLimit = Math.max(projectLimit, INITIAL_PROJECT_LIMIT)
  const baseVisibleProjects = useMemo(
    () => projects.slice(0, visibleProjectLimit),
    [projects, visibleProjectLimit],
  )
  const activeHiddenProject =
    activeProjectId && !baseVisibleProjects.some((project) => project.id === activeProjectId)
      ? projects.find((project) => project.id === activeProjectId) ?? null
      : null
  const visibleProjects = activeHiddenProject ? [...baseVisibleProjects, activeHiddenProject] : baseVisibleProjects
  const remainingProjectCount = Math.max(0, projects.length - baseVisibleProjects.length)
  const visibleSessions = sessions.slice(0, sessionLimit)
  const remainingSessionCount = Math.max(0, sessions.length - sessionLimit)
  const pinnedSessions = visibleSessions.filter((session) => session.pinned)
  const unpinnedSessions = visibleSessions.filter((session) => !session.pinned)

  useEffect(() => {
    setProjectLimit(INITIAL_PROJECT_LIMIT)
  }, [projects.length])

  useEffect(() => {
    if (collapsed) return
    const viewport = scrollAreaRef.current?.querySelector<HTMLDivElement>("[data-scroll-viewport]")
    viewport?.scrollTo({ top: 0 })
  }, [collapsed])

  const renderSessionRow = (session: SessionSummary) => {
    const title = sessionTitle(session)
    return (
      <div
        className="session-row"
        key={session.session_id}
        onMouseEnter={() => setHoveredSessionId(session.session_id)}
        onMouseLeave={() => {
          if (openMenuId !== session.session_id) setHoveredSessionId(null)
        }}
      >
        {renamingId === session.session_id ? (
          <input
            autoFocus
            className="session-rename-input"
            value={renameValue}
            onChange={(event) => setRenameValue(event.target.value)}
            onBlur={() => {
              void onRenameSession(session.session_id, renameValue)
              setRenamingId(null)
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                void onRenameSession(session.session_id, renameValue)
                setRenamingId(null)
                return
              }
              if (event.key === "Escape") {
                setRenamingId(null)
              }
            }}
            onClick={(event) => event.stopPropagation()}
            type="text"
          />
        ) : (
          <button
            className={cn("sidebar-item", session.session_id === activeSessionId && "active")}
            onClick={() => onSelectSession(session.session_id)}
            type="button"
          >
            <span className="session-title-text">{title}</span>
          </button>
        )}

        {(hoveredSessionId === session.session_id || openMenuId === session.session_id) ? (
          <div className="session-menu-wrapper" ref={openMenuId === session.session_id ? menuRef : undefined}>
            <button
              className="session-menu-btn"
              onClick={(event) => {
                event.stopPropagation()
                setOpenMenuId(openMenuId === session.session_id ? null : session.session_id)
              }}
              type="button"
            >
              <MoreVertical className="size-3.5" />
            </button>
            {openMenuId === session.session_id ? (
              <div className="session-menu-dropdown">
                <button
                  className="session-menu-item"
                  onClick={() => {
                    onPinSession(session.session_id)
                    setOpenMenuId(null)
                  }}
                  type="button"
                >
                  {session.pinned ? <PinOff className="size-3.5" /> : <Pin className="size-3.5" />}
                  <span>{session.pinned ? "Unpin" : "Pin"}</span>
                </button>
                <button
                  className="session-menu-item"
                  onClick={() => {
                    setRenameValue(session.title || title)
                    setRenamingId(session.session_id)
                    setOpenMenuId(null)
                  }}
                  type="button"
                >
                  <Pencil className="size-3.5" />
                  <span>Rename</span>
                </button>
                <button
                  className="session-menu-item"
                  onClick={() => {
                    setOpenMenuId(null)
                    onAddToProject?.(session.session_id)
                  }}
                  type="button"
                >
                  <FolderOpen className="size-3.5" />
                  <span>Add to project</span>
                </button>
                <div className="session-menu-divider" />
                <button
                  className="session-menu-item danger"
                  onClick={() => {
                    setOpenMenuId(null)
                    if (window.confirm(`Delete "${title}"?`)) {
                      onDeleteSession(session.session_id)
                    }
                  }}
                  type="button"
                >
                  <Trash2 className="size-3.5" />
                  <span>Delete</span>
                </button>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    )
  }

  useEffect(() => {
    if (!openMenuId) return

    function handleOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpenMenuId(null)
      }
    }

    document.addEventListener("mousedown", handleOutside)
    return () => document.removeEventListener("mousedown", handleOutside)
  }, [openMenuId])

  if (collapsed) {
    return (
      <div className="sidebar-rail" aria-label="Geneva navigation">
        <div className="sidebar-rail-stack">
          <RailButton className="sidebar-rail-brand" label="Expand sidebar" onClick={onToggleCollapsed}>
            <GenevaMark className="sidebar-rail-mark" variant="dot" />
          </RailButton>
          <RailButton label="New chat" onClick={onNewChat}>
            <Plus className="size-4" />
          </RailButton>
          <RailButton label="Search" onClick={onOpenSearch}>
            <Search className="size-4" />
          </RailButton>
          <RailButton active={activeTab === "chat"} label="Chats" onClick={() => onTabChange("chat")}>
            <MessageSquare className="size-4" />
          </RailButton>
          <RailButton active={activeTab === "skill"} label="Customize" onClick={() => onTabChange("skill")}>
            <Sparkle className="size-4" />
          </RailButton>
          <RailButton label="Library" onClick={onOpenSource}>
            <Archive className="size-4" />
          </RailButton>
          <RailButton label="Artifacts" onClick={onOpenArtifacts}>
            <Box className="size-4" />
          </RailButton>
        </div>
        <div className="sidebar-rail-stack">
          <RailButton label={`${memoryStats.active} memories`} onClick={onOpenSettings}>
            <span className="sidebar-rail-avatar">B</span>
          </RailButton>
          <RailButton label="Settings" onClick={onOpenSettings}>
            <Settings2 className="size-4" />
          </RailButton>
        </div>
      </div>
    )
  }

  return (
    <div className="sidebar-panel">
      <div className="sidebar-header">
        <button className="sidebar-brand" onClick={onNewChat} type="button">
          <GenevaMark className="brand-mark" variant="dot" />
          <span>Geneva</span>
        </button>
        <div className="sidebar-header-actions">
          <Button aria-label="Search" onClick={onOpenSearch} size="compactIcon" variant="quiet">
            <Search className="size-4" />
          </Button>
          <Button aria-label="Collapse sidebar" onClick={onToggleCollapsed} size="compactIcon" variant="quiet">
            <PanelLeftClose className="size-4" />
          </Button>
        </div>
      </div>

      <div className="sidebar-command-stack">
        <Button className="sidebar-primary-action" onClick={onNewChat} variant="sidebar">
          <Plus className="size-4" />
          New chat
        </Button>
        <Button className="sidebar-search-action" onClick={onOpenSearch} variant="sidebar">
          <Search className="size-4" />
          <span>Search</span>
          <span className="sidebar-shortcut">Cmd K</span>
        </Button>
        <Button
          aria-label="Customize"
          className={cn("sidebar-skills-action", activeTab === "skill" && "active")}
          onClick={() => onTabChange(activeTab === "skill" ? "chat" : "skill")}
          variant="sidebar"
        >
          <Sparkle className="size-4" />
          <span>Customize</span>
        </Button>
        <Button className="sidebar-open-source-action" onClick={onOpenSource} variant="sidebar">
          <Archive className="size-4" />
          <span>Library</span>
        </Button>
        <Button className="sidebar-artifacts-action" onClick={onOpenArtifacts} variant="sidebar">
          <Box className="size-4" />
          <span>Artifacts</span>
        </Button>
      </div>

      <ScrollArea className="mt-5 min-h-0 flex-1 px-3 pr-0" ref={scrollAreaRef}>
        <div className="pr-3">
        <SectionTitle label="Projects">
          <span className="project-section-tools">
            <span className="project-list-count">{formatSidebarCount(projects.length)}</span>
            {projectsLoading && projects.length > 0 ? <span className="project-sync-pill">Syncing</span> : null}
            <button
              className="sidebar-section-icon-button"
              onClick={onCreateProject}
              title="New project"
              type="button"
            >
              <Plus className="size-3.5" />
            </button>
          </span>
        </SectionTitle>
        <nav aria-busy={projectsLoading} className="mb-5 space-y-0.5">
          {projectsError ? (
            <div className="sidebar-project-error" role="status">
              <AlertCircle className="size-3.5" />
              <span>{projectsError}</span>
              {onRetryProjects ? (
                <button onClick={onRetryProjects} type="button">
                  <RefreshCw className="size-3" />
                  Retry
                </button>
              ) : null}
            </div>
          ) : null}
          {projectsLoading && projects.length === 0 ? (
            <div aria-label="Loading projects" className="project-list-skeleton">
              <span />
              <span />
              <span />
            </div>
          ) : null}
          {visibleProjects.map((project) => {
            const pendingCount = project.todos.filter((todo) => !todo.done).length
            return (
              <div
                className={cn("project-item", activeProjectId === project.id && "active")}
                key={project.id}
              >
                <span className="project-dot" style={{ background: project.color }} />
                <button className="project-main-button" onClick={() => onSelectProject(project)} type="button">
                  <span className="truncate text-[14px]">{project.name}</span>
                  <span className="project-session-count">{formatSidebarCount(project.session_count)} chats</span>
                </button>
                {pendingCount > 0 ? <span className="todo-count">{formatSidebarCount(pendingCount)}</span> : null}
                <span className="project-hover-actions">
                  <button
                    aria-label={`New chat in ${project.name}`}
                    onClick={() => onOpenProjectChat(project)}
                    title="New chat"
                    type="button"
                  >
                    <MessageCircle className="size-3.5" />
                  </button>
                  <button
                    aria-label={`View ${project.name}`}
                    onClick={() => onSelectProject(project)}
                    title="View project"
                    type="button"
                  >
                    <FolderOpen className="size-3.5" />
                  </button>
                </span>
              </div>
            )
          })}
          {projects.length === 0 && !projectsLoading ? (
            <p className="project-empty">{projectsError ? "Projects could not load" : "No projects yet"}</p>
          ) : null}
          <button className="sidebar-item mt-1 w-full" onClick={onCreateProject} type="button">
            <Plus className="size-4 mr-2 opacity-60" />
            <span className="opacity-80">Add New Project</span>
          </button>
          {projects.length > INITIAL_PROJECT_LIMIT ? (
            <button
              className="project-see-all"
              onClick={() => {
                setProjectLimit((current) =>
                  remainingProjectCount > 0 ? current + PROJECT_PAGE_SIZE : INITIAL_PROJECT_LIMIT,
                )
              }}
              type="button"
            >
              {remainingProjectCount > 0
                ? `Show ${Math.min(PROJECT_PAGE_SIZE, remainingProjectCount)} more`
                : "Show fewer projects"}
            </button>
          ) : null}
        </nav>
        <nav className="space-y-1 pb-8">
          {sessions.length === 0 ? (
            <p className="px-2 py-2 text-sm text-muted-foreground">No saved sessions yet</p>
          ) : (
            <>
              {pinnedSessions.length > 0 ? (
                <div className="sidebar-pinned-section">
                  <p className="sidebar-section-label">Pinned</p>
                  {pinnedSessions.map(renderSessionRow)}
                </div>
              ) : null}
              {unpinnedSessions.length > 0 ? (
                <>
                  <SectionTitle label="Recents" />
                  {groupSessionsByBucket(unpinnedSessions).map(({ bucket, label, sessions: bucketSessions }) => (
                    <div key={bucket}>
                      <p className="px-2 pt-3 pb-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground/60 select-none">
                        {label}
                      </p>
                      {bucketSessions.map(renderSessionRow)}
                    </div>
                  ))}
                </>
              ) : null}
            </>
          )}
        </nav>
        {remainingSessionCount > 0 ? (
          <button
            className="project-see-all"
            onClick={() => setSessionLimit(sessions.length)}
            type="button"
          >
            All Chats
          </button>
        ) : null}
        </div>
      </ScrollArea>

      <div className="sidebar-footer">
        <div className="sidebar-profile-shell">
          <div className="sidebar-profile-avatar">G</div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-[14px] font-semibold text-foreground">Geneva</div>
            <div className="truncate text-[12px] text-muted-foreground">{memoryStats.active} memories</div>
          </div>
          <Button aria-label="Open settings" onClick={onOpenSettings} size="compactIcon" variant="quiet">
            <Settings2 className="size-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

function RailButton({
  active = false,
  children,
  className,
  disabled = false,
  label,
  onClick,
}: {
  active?: boolean
  children: ReactNode
  className?: string
  disabled?: boolean
  label: string
  onClick: () => void
}) {
  return (
    <button
      aria-label={label}
      className={cn("sidebar-rail-button", className, active && "active")}
      disabled={disabled}
      onClick={onClick}
      title={label}
      type="button"
    >
      {children}
    </button>
  )
}

function SectionTitle({
  children,
  className,
  label,
}: {
  children?: ReactNode
  className?: string
  label: string
}) {
  return (
    <div className={cn("sidebar-section-title", className)}>
      <span>{label}</span>
      {children}
    </div>
  )
}

export function sessionTitle(session: SessionSummary): string {
  if (session.title) return session.title
  if (session.message_count && Number(session.message_count) > 0) {
    return `Chat with ${session.message_count} messages`
  }
  if (session.updated_at) return `Session ${session.updated_at.slice(0, 10)}`
  return session.session_id.slice(0, 12)
}

function formatSidebarCount(value: number): string {
  if (value > 99) return "99+"
  return String(value)
}

const DATE_BUCKET_LABELS: Record<string, string> = {
  today: "Today",
  yesterday: "Yesterday",
  three_days_ago: "Three days ago",
  this_week: "This week",
  two_weeks_ago: "Two weeks ago",
  three_weeks_ago: "Three weeks ago",
  one_month: "One month",
  older: "Older",
}

function groupSessionsByBucket(
  sessions: SessionSummary[],
): Array<{ bucket: string; label: string; sessions: SessionSummary[] }> {
  const order = ["today", "yesterday", "three_days_ago", "this_week", "two_weeks_ago", "three_weeks_ago", "one_month", "older"]
  const map = new Map<string, SessionSummary[]>()
  for (const session of sessions) {
    const bucket = session.date_bucket || "older"
    if (!map.has(bucket)) map.set(bucket, [])
    map.get(bucket)!.push(session)
  }
  const result: Array<{ bucket: string; label: string; sessions: SessionSummary[] }> = []
  for (const bucket of order) {
    if (map.has(bucket)) {
      result.push({
        bucket,
        label: DATE_BUCKET_LABELS[bucket] ?? bucket,
        sessions: map.get(bucket)!,
      })
    }
  }
  for (const [bucket, items] of map) {
    if (!order.includes(bucket)) {
      result.push({ bucket, label: DATE_BUCKET_LABELS[bucket] ?? bucket, sessions: items })
    }
  }
  return result
}
