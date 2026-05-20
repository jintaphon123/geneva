import {
  Children,
  type KeyboardEvent,
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react"
import {
  ClipboardList,
  Database,
  FileText,
  FolderOpen,
  Loader2,
  MessageSquare,
  Search,
  X,
} from "lucide-react"

import { sessionTitle } from "@/components/Sidebar"
import { searchGeneva } from "@/lib/api"
import { cn } from "@/lib/utils"
import type { Project, SearchResult, SearchResultType, SessionSummary } from "@/types"

type SearchOverlayProps = {
  open: boolean
  sessions: SessionSummary[]
  projects: Project[]
  activeSessionId: string | null
  activeProjectId: string | null
  onClose: () => void
  onSelectSession: (sessionId: string) => void
  onSelectProject: (project: Project) => void
  onOpenMemory?: () => void
}

type SearchOverlayItem = {
  key: string
  type: SearchResultType
  title: string
  subtitle: string
  snippet?: string
  badges: string[]
  result?: SearchResult
  sessionId?: string
  projectId?: string
  projectColor?: string
  active?: boolean
}

const SEARCH_TYPE_ORDER: SearchResultType[] = ["chat", "project", "memory", "source", "research_report"]

const SEARCH_TYPE_META: Record<string, { label: string; icon: typeof MessageSquare }> = {
  chat: { label: "Chats", icon: MessageSquare },
  project: { label: "Projects", icon: FolderOpen },
  memory: { label: "Memories", icon: Database },
  source: { label: "Sources", icon: FileText },
  research_report: { label: "Research reports", icon: ClipboardList },
}

const SEARCH_EXAMPLES = ["Agent Harness", "project sources", "memory review"]

export function SearchOverlay({
  open,
  sessions,
  projects,
  activeSessionId,
  activeProjectId,
  onClose,
  onSelectSession,
  onSelectProject,
  onOpenMemory,
}: SearchOverlayProps) {
  const [query, setQuery] = useState("")
  const [activeIndex, setActiveIndex] = useState(0)
  const [scopeProjectOnly, setScopeProjectOnly] = useState(false)
  const [payload, setPayload] = useState<SearchPayloadState>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement | null>(null)
  const normalizedQuery = query.trim().toLowerCase()
  const activeProject = activeProjectId
    ? projects.find((project) => project.id === activeProjectId) ?? null
    : null

  const matchedSessions = useMemo(() => {
    const source = normalizedQuery
      ? sessions.filter((session) =>
          [
            sessionTitle(session),
            session.project_name ?? "",
            session.provider ?? "",
            session.model ?? "",
          ].some((value) => value.toLowerCase().includes(normalizedQuery)),
        )
      : sessions
    return source.slice(0, 6)
  }, [normalizedQuery, sessions])

  const matchedProjects = useMemo(() => {
    const source = normalizedQuery
      ? projects.filter((project) =>
          [project.name, project.description, project.context_md, ...project.todos.map((todo) => todo.text)].some(
            (value) => value.toLowerCase().includes(normalizedQuery),
          ),
        )
      : projects
    return source.slice(0, 6)
  }, [normalizedQuery, projects])

  const localGroups = useMemo(
    () => [
      {
        label: "Chats",
        items: matchedSessions.map<SearchOverlayItem>((session) => ({
          key: `session-${session.session_id}`,
          type: "chat",
          title: sessionTitle(session),
          subtitle: session.project_name || session.model || "Conversation",
          badges: ["chat"],
          sessionId: session.session_id,
          projectId: session.project_id,
          projectColor: session.project_color,
          active: session.session_id === activeSessionId,
        })),
      },
      {
        label: "Projects",
        items: matchedProjects.map<SearchOverlayItem>((project) => ({
          key: `project-${project.id}`,
          type: "project",
          title: project.name,
          subtitle: `${project.session_count} chats · ${project.todos.filter((todo) => !todo.done).length} open`,
          badges: ["project"],
          projectId: project.id,
          projectColor: project.color,
          active: project.id === activeProjectId,
        })),
      },
    ],
    [activeProjectId, activeSessionId, matchedProjects, matchedSessions],
  )

  const backendGroups = useMemo(() => {
    if (!normalizedQuery || !payload) return []
    const known = new Set(SEARCH_TYPE_ORDER)
    const orderedGroups = SEARCH_TYPE_ORDER.map((type) => ({
      label: SEARCH_TYPE_META[type]?.label ?? type,
      items: (payload.groups[type]?.results ?? []).map((result) => resultToItem(result, projects, activeSessionId)),
    }))
    const remainingGroups = Object.values(payload.groups)
      .filter((group) => !known.has(group.type))
      .map((group) => ({
        label: group.type,
        items: group.results.map((result) => resultToItem(result, projects, activeSessionId)),
      }))
    return [...orderedGroups, ...remainingGroups].filter((group) => group.items.length > 0)
  }, [activeSessionId, normalizedQuery, payload, projects])

  const groups = normalizedQuery && payload ? backendGroups : localGroups
  const visibleItems = groups.flatMap((group) => group.items)
  const hasBackendResults = normalizedQuery && payload && payload.count > 0
  const showLocalFallback = normalizedQuery && !loading && (!hasBackendResults || Boolean(error))

  useEffect(() => {
    if (!open) return
    setQuery("")
    setPayload(null)
    setError(null)
    setActiveIndex(0)
    setScopeProjectOnly(Boolean(activeProjectId))
    window.requestAnimationFrame(() => inputRef.current?.focus())
  }, [activeProjectId, open])

  useEffect(() => {
    if (!open || !normalizedQuery) {
      setPayload(null)
      setLoading(false)
      setError(null)
      return
    }

    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      setLoading(true)
      setError(null)
      searchGeneva({
        query: normalizedQuery,
        projectId: scopeProjectOnly ? activeProjectId : null,
        limit: 24,
        signal: controller.signal,
      })
        .then((nextPayload) => setPayload(nextPayload))
        .catch((nextError: unknown) => {
          if (isAbortError(nextError)) return
          setPayload(null)
          setError(nextError instanceof Error ? nextError.message : "Search failed")
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false)
        })
    }, 110)

    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [activeProjectId, normalizedQuery, open, scopeProjectOnly])

  useEffect(() => {
    setActiveIndex(0)
  }, [normalizedQuery, scopeProjectOnly])

  useEffect(() => {
    if (!visibleItems.length) {
      setActiveIndex(0)
      return
    }
    setActiveIndex((index) => Math.min(index, visibleItems.length - 1))
  }, [visibleItems.length])

  const selectItem = useCallback(
    (item: SearchOverlayItem) => {
      if (item.sessionId) {
        onSelectSession(item.sessionId)
        onClose()
        return
      }

      if (item.projectId) {
        const project = projects.find((candidate) => candidate.id === item.projectId)
        if (project) {
          onSelectProject(project)
          onClose()
          return
        }
      }

      if (item.result?.type === "memory") {
        onOpenMemory?.()
        onClose()
        return
      }

      const chatAction = item.result?.actions.find((action) => action.id === "open_chat")
      const sessionId = stringValue(chatAction?.session_id)
      if (sessionId) {
        onSelectSession(sessionId)
        onClose()
        return
      }

      const projectAction = item.result?.actions.find(
        (action) => action.id === "open_project" || action.id === "open_source",
      )
      const projectId = stringValue(projectAction?.project_id)
      const project = projectId ? projects.find((candidate) => candidate.id === projectId) : null
      if (project) onSelectProject(project)
      onClose()
    },
    [onClose, onOpenMemory, onSelectProject, onSelectSession, projects],
  )

  function handleInputKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Escape") {
      event.preventDefault()
      onClose()
      return
    }

    if (!visibleItems.length) return

    if (event.key === "ArrowDown") {
      event.preventDefault()
      setActiveIndex((index) => (index + 1) % visibleItems.length)
      return
    }
    if (event.key === "ArrowUp") {
      event.preventDefault()
      setActiveIndex((index) => (index - 1 + visibleItems.length) % visibleItems.length)
      return
    }
    if (event.key === "Enter") {
      event.preventDefault()
      selectItem(visibleItems[activeIndex] ?? visibleItems[0])
    }
  }

  if (!open) return null

  return (
    <div
      className="search-overlay-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
      role="presentation"
    >
      <section aria-label="Search Geneva" aria-modal="true" className="search-overlay-panel" role="dialog">
        <div className="search-overlay-input-row">
          <Search className="size-4" />
          <input
            aria-activedescendant={visibleItems[activeIndex]?.key}
            aria-label="Search chats, projects, memories, sources, and reports"
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={handleInputKeyDown}
            placeholder="Search Geneva..."
            ref={inputRef}
            value={query}
          />
          {loading ? <Loader2 className="search-spinner size-4" /> : <span className="search-kbd">⌘K</span>}
          <button aria-label="Close search" onClick={onClose} type="button">
            <X className="size-4" />
          </button>
        </div>

        {activeProject ? (
          <button
            className={cn("search-scope-row", scopeProjectOnly && "active")}
            onClick={() => setScopeProjectOnly((enabled) => !enabled)}
            type="button"
          >
            <span className="project-dot" style={{ background: activeProject.color }} />
            <span>Search this project</span>
            <small>{activeProject.name}</small>
          </button>
        ) : null}

        <div className="search-overlay-results" role="listbox">
          {groups.map((group) => (
            <SearchSection
              emptyLabel={normalizedQuery ? `No matching ${group.label.toLowerCase()}` : "Nothing here yet"}
              key={group.label}
              title={group.label}
            >
              {group.items.map((item) => {
                const index = visibleItems.findIndex((candidate) => candidate.key === item.key)
                return (
                  <SearchResultRow
                    active={index === activeIndex}
                    item={item}
                    key={item.key}
                    onSelect={() => selectItem(item)}
                  />
                )
              })}
            </SearchSection>
          ))}

          {loading ? <p className="search-overlay-status">Searching Geneva...</p> : null}
          {error ? <p className="search-overlay-status">Search is using local matches. {error}</p> : null}
          {showLocalFallback ? <LocalFallback groups={localGroups} onSelect={selectItem} /> : null}
          {!visibleItems.length && !loading ? <SearchEmpty query={normalizedQuery} onExample={setQuery} /> : null}
        </div>
      </section>
    </div>
  )
}

type SearchPayloadState = Awaited<ReturnType<typeof searchGeneva>> | null

function SearchSection({
  children,
  emptyLabel,
  title,
}: {
  children: ReactNode
  emptyLabel: string
  title: string
}) {
  return (
    <section className="search-result-section">
      <h2>{title}</h2>
      {Children.count(children) > 0 ? children : <p>{emptyLabel}</p>}
    </section>
  )
}

function SearchResultRow({
  active,
  item,
  onSelect,
}: {
  active: boolean
  item: SearchOverlayItem
  onSelect: () => void
}) {
  const Icon = SEARCH_TYPE_META[item.type]?.icon ?? FileText
  return (
    <button
      aria-selected={active}
      className={cn("search-result-row", active && "active", item.active && "current")}
      id={item.key}
      onClick={onSelect}
      role="option"
      type="button"
    >
      <span className="search-result-icon">
        <Icon className="size-4" />
      </span>
      <span className="search-result-copy">
        <strong>{item.title}</strong>
        <small>{item.subtitle}</small>
        {item.snippet ? <span className="search-result-snippet">{item.snippet}</span> : null}
      </span>
      <span className="search-result-meta">
        {item.badges.slice(0, 3).map((badge) => (
          <span className="search-result-badge" key={`${item.key}-${badge}`}>
            {badge}
          </span>
        ))}
        {item.projectColor ? <span className="project-dot" style={{ background: item.projectColor }} /> : null}
      </span>
    </button>
  )
}

function LocalFallback({
  groups,
  onSelect,
}: {
  groups: Array<{ label: string; items: SearchOverlayItem[] }>
  onSelect: (item: SearchOverlayItem) => void
}) {
  const fallbackItems = groups.flatMap((group) => group.items).slice(0, 4)
  if (!fallbackItems.length) return null
  return (
    <section className="search-result-section">
      <h2>Local matches</h2>
      {fallbackItems.map((item) => (
        <SearchResultRow active={false} item={item} key={`fallback-${item.key}`} onSelect={() => onSelect(item)} />
      ))}
    </section>
  )
}

function SearchEmpty({ query, onExample }: { query: string; onExample: (value: string) => void }) {
  return (
    <div className="search-empty-examples">
      <p>{query ? "No results yet." : "Try a search across your brain."}</p>
      <div>
        <span>Try</span>
        {SEARCH_EXAMPLES.map((example) => (
          <button key={example} onClick={() => onExample(example)} type="button">
            {example}
          </button>
        ))}
      </div>
    </div>
  )
}

function resultToItem(
  result: SearchResult,
  projects: Project[],
  activeSessionId: string | null,
): SearchOverlayItem {
  const project = result.project_id ? projects.find((candidate) => candidate.id === result.project_id) ?? null : null
  return {
    key: `${result.type}-${result.id}`,
    type: result.type,
    title: result.title,
    subtitle: subtitleForResult(result, project),
    snippet: result.snippet,
    badges: result.badges.length ? result.badges : [String(result.type)],
    result,
    sessionId: result.session_id ?? undefined,
    projectId: result.type === "project" ? result.project_id ?? result.id : result.project_id ?? undefined,
    projectColor: project?.color,
    active: Boolean(result.session_id && result.session_id === activeSessionId),
  }
}

function subtitleForResult(result: SearchResult, project: Project | null): string {
  const fields = result.matched_fields.slice(0, 2).join(", ")
  if (project && fields) return `${project.name} · ${fields}`
  if (project) return project.name
  if (fields) return fields
  return SEARCH_TYPE_META[result.type]?.label ?? "Geneva"
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError"
}
