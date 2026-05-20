import { type ReactNode, useCallback, useEffect, useMemo, useState } from "react"
import { motion } from "framer-motion"
import {
  Archive,
  Brain,
  Check,
  Edit3,
  Eye,
  GitMerge,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  SlidersHorizontal,
  Trash2,
  X,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  addMemory,
  approveMemoryWriteEvent,
  archiveMemory,
  deleteMemory,
  fetchMemory,
  fetchMemoryBrowserStats,
  listMemories,
  listMemoryConflicts,
  listMemoryWriteEvents,
  resolveMemoryConflict,
  undoMemoryWriteEvent,
  updateMemory,
} from "@/lib/api"
import { cn } from "@/lib/utils"
import type { MemoryBrowserStats, MemoryConflict, MemoryItem, MemoryWriteEvent } from "@/types"

const PAGE_SIZE = 20
const MEMORY_TYPES = ["all", "user", "feedback", "project", "reference", "episodic"]
const MEMORY_STATUSES = ["active", "archived", "superseded", "expired", "deleted", "all"]

export function MemoryBrowser() {
  const [items, setItems] = useState<MemoryItem[]>([])
  const [total, setTotal] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(false)
  const [query, setQuery] = useState("")
  const [debouncedQuery, setDebouncedQuery] = useState("")
  const [typeFilter, setTypeFilter] = useState("all")
  const [statusFilter, setStatusFilter] = useState("active")
  const [stats, setStats] = useState<MemoryBrowserStats>({})
  const [error, setError] = useState<string | null>(null)
  const [addingMemory, setAddingMemory] = useState(false)
  const [editingMemory, setEditingMemory] = useState<MemoryItem | null>(null)
  const [inspectingMemory, setInspectingMemory] = useState<MemoryItem | null>(null)
  const [conflicts, setConflicts] = useState<MemoryConflict[]>([])
  const [conflictTotal, setConflictTotal] = useState(0)
  const [conflictLoading, setConflictLoading] = useState(false)
  const [conflictError, setConflictError] = useState<string | null>(null)
  const [mergeConflict, setMergeConflict] = useState<MemoryConflict | null>(null)
  const [resolvingConflictId, setResolvingConflictId] = useState<string | null>(null)
  const [writeEvents, setWriteEvents] = useState<MemoryWriteEvent[]>([])
  const [writeEventTotal, setWriteEventTotal] = useState(0)
  const [writeEventLoading, setWriteEventLoading] = useState(false)
  const [writeEventError, setWriteEventError] = useState<string | null>(null)
  const [resolvingWriteEventId, setResolvingWriteEventId] = useState<string | null>(null)
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false)

  useEffect(() => {
    const timeout = window.setTimeout(() => setDebouncedQuery(query.trim()), 300)
    return () => window.clearTimeout(timeout)
  }, [query])

  const refreshStats = useCallback(async () => {
    try {
      setStats(await fetchMemoryBrowserStats())
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load memory stats")
      setStats({})
    }
  }, [])

  const refreshConflicts = useCallback(async () => {
    setConflictLoading(true)
    try {
      setConflictError(null)
      const result = await listMemoryConflicts({ status: "open", limit: 8, offset: 0 })
      setConflicts(result.items)
      setConflictTotal(result.total)
    } catch (err) {
      setConflictError(err instanceof Error ? err.message : "Could not load memory conflicts")
      setConflicts([])
      setConflictTotal(0)
    } finally {
      setConflictLoading(false)
    }
  }, [])

  const refreshWriteEvents = useCallback(async () => {
    setWriteEventLoading(true)
    try {
      setWriteEventError(null)
      const result = await listMemoryWriteEvents({ status: "draft", limit: 8, offset: 0 })
      setWriteEvents(result.items)
      setWriteEventTotal(result.total)
    } catch (err) {
      setWriteEventError(err instanceof Error ? err.message : "Could not load memory write review queue")
      setWriteEvents([])
      setWriteEventTotal(0)
    } finally {
      setWriteEventLoading(false)
    }
  }, [])

  const loadPage = useCallback(
    async (offset: number, append = false) => {
      setLoading(true)
      try {
        setError(null)
        const result = await listMemories({
          type: typeFilter === "all" ? undefined : typeFilter,
          status: statusFilter,
          q: debouncedQuery || undefined,
          limit: PAGE_SIZE,
          offset,
        })
        setItems((current) => (append ? [...current, ...result.items] : result.items))
        setTotal(result.total)
        setHasMore(result.has_more)
      } finally {
        setLoading(false)
      }
    },
    [debouncedQuery, statusFilter, typeFilter],
  )

  useEffect(() => {
    void loadPage(0)
    void refreshStats()
    void refreshConflicts()
    void refreshWriteEvents()
  }, [loadPage, refreshConflicts, refreshStats, refreshWriteEvents])

  const handleRefresh = useCallback(async () => {
    await Promise.all([loadPage(0), refreshStats(), refreshConflicts(), refreshWriteEvents()])
  }, [loadPage, refreshConflicts, refreshStats, refreshWriteEvents])

  const handleResolveConflict = useCallback(
    async (
      conflict: MemoryConflict,
      resolution: "keep_existing" | "replace" | "merge",
      mergedContent?: string,
    ) => {
      setResolvingConflictId(conflict.id)
      try {
        await resolveMemoryConflict(conflict.id, resolution, mergedContent)
        setMergeConflict(null)
        await handleRefresh()
      } catch (err) {
        setConflictError(err instanceof Error ? err.message : "Could not resolve memory conflict")
      } finally {
        setResolvingConflictId(null)
      }
    },
    [handleRefresh],
  )

  const handleArchive = useCallback(
    async (id: string) => {
      await archiveMemory(id)
      await handleRefresh()
    },
    [handleRefresh],
  )

  const handleDelete = useCallback(
    async (id: string) => {
      await deleteMemory(id)
      await handleRefresh()
    },
    [handleRefresh],
  )

  const handleInspect = useCallback(async (memory: MemoryItem) => {
    setInspectingMemory(memory)
    try {
      setInspectingMemory(await fetchMemory(memory.id))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load memory detail")
    }
  }, [])

  const handleResolveWriteEvent = useCallback(
    async (event: MemoryWriteEvent, action: "approve" | "undo") => {
      setResolvingWriteEventId(event.id)
      try {
        if (action === "approve") {
          await approveMemoryWriteEvent(event.id)
        } else {
          await undoMemoryWriteEvent(event.id)
        }
        await handleRefresh()
      } catch (err) {
        setWriteEventError(err instanceof Error ? err.message : "Could not update memory write event")
      } finally {
        setResolvingWriteEventId(null)
      }
    },
    [handleRefresh],
  )

  const statText = useMemo(() => {
    const byStatus = stats.by_status ?? {}
    const byType = stats.by_type ?? {}
    const byConflictStatus = stats.conflicts_by_status ?? {}
    return [
      `${byStatus.active ?? 0} active`,
      `${byType.episodic ?? 0} episodic`,
      `${byType.feedback ?? 0} feedback`,
      `${byType.project ?? 0} project`,
      formatCount(byConflictStatus.open ?? conflictTotal, "conflict"),
      `${byStatus.deleted ?? 0} deleted`,
    ]
  }, [conflictTotal, stats])

  return (
    <div className="memory-browser">
      <div className="memory-browser-header">
        <div>
          <h2>Memory</h2>
          <p>{total} matching memories</p>
        </div>
        <Button onClick={() => setAddingMemory(true)} type="button">
          <Plus className="size-4" />
          Add Memory
        </Button>
      </div>

      <button
        aria-expanded={mobileFiltersOpen}
        className="memory-mobile-filter-toggle"
        onClick={() => setMobileFiltersOpen(true)}
        type="button"
      >
        <SlidersHorizontal className="size-4" />
        Filters
      </button>
      {mobileFiltersOpen ? (
        <button
          aria-label="Close memory filters overlay"
          className="memory-filter-backdrop"
          onClick={() => setMobileFiltersOpen(false)}
          type="button"
        />
      ) : null}

      <div className={cn("memory-filter-row", mobileFiltersOpen && "mobile-open")}>
        <button
          aria-label="Close memory filters"
          className="memory-mobile-filter-close"
          onClick={() => setMobileFiltersOpen(false)}
          type="button"
        >
          <X className="size-4" />
        </button>
        <div className="memory-search-wrap">
          <Search className="size-4" />
          <input
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search memories..."
            value={query}
          />
        </div>
        <select onChange={(event) => setTypeFilter(event.target.value)} value={typeFilter}>
          {MEMORY_TYPES.map((type) => (
            <option key={type} value={type}>
              {type === "all" ? "All" : titleCase(type)}
            </option>
          ))}
        </select>
        <select onChange={(event) => setStatusFilter(event.target.value)} value={statusFilter}>
          {MEMORY_STATUSES.map((status) => (
            <option key={status} value={status}>
              {titleCase(status)}
            </option>
          ))}
        </select>
      </div>

      <div className="memory-stat-row">
        {statText.map((stat) => (
          <span key={stat}>{stat}</span>
        ))}
      </div>

      <ConflictReviewQueue
        conflicts={conflicts}
        error={conflictError}
        loading={conflictLoading}
        onMerge={setMergeConflict}
        onRefresh={() => void refreshConflicts()}
        onResolve={(conflict, resolution) => void handleResolveConflict(conflict, resolution)}
        resolvingConflictId={resolvingConflictId}
        total={conflictTotal}
      />

      <MemoryWriteReviewQueue
        error={writeEventError}
        events={writeEvents}
        loading={writeEventLoading}
        onRefresh={() => void refreshWriteEvents()}
        onResolve={(event, action) => void handleResolveWriteEvent(event, action)}
        resolvingEventId={resolvingWriteEventId}
        total={writeEventTotal}
      />

      <div className="memory-list">
        {error ? <div className="memory-error">{error}</div> : null}
        {items.map((item, index) => (
          <MemoryCard
            key={item.id}
            memory={item}
            onArchive={() => void handleArchive(item.id)}
            onDelete={() => void handleDelete(item.id)}
            onEdit={() => setEditingMemory(item)}
            onInspect={() => void handleInspect(item)}
            order={index}
          />
        ))}
        {loading ? <LoadingSpinner /> : null}
        {!loading && items.length === 0 ? <EmptyMemoryState /> : null}
        {hasMore ? (
          <Button
            className="memory-load-more"
            disabled={loading}
            onClick={() => void loadPage(items.length, true)}
            type="button"
            variant="subtle"
          >
            Load more
          </Button>
        ) : null}
      </div>

      {addingMemory ? (
        <AddMemoryModal
          onClose={() => setAddingMemory(false)}
          onSaved={() => {
            setAddingMemory(false)
            void handleRefresh()
          }}
        />
      ) : null}
      {editingMemory ? (
        <EditMemoryModal
          memory={editingMemory}
          onClose={() => setEditingMemory(null)}
          onSaved={() => {
            setEditingMemory(null)
            void handleRefresh()
          }}
        />
      ) : null}
      {inspectingMemory ? (
        <MemoryDetailModal memory={inspectingMemory} onClose={() => setInspectingMemory(null)} />
      ) : null}
      {mergeConflict ? (
        <MergeConflictModal
          conflict={mergeConflict}
          onClose={() => setMergeConflict(null)}
          onResolve={(mergedContent) =>
            void handleResolveConflict(mergeConflict, "merge", mergedContent)
          }
          resolving={resolvingConflictId === mergeConflict.id}
        />
      ) : null}
    </div>
  )
}

function ConflictReviewQueue({
  conflicts,
  error,
  loading,
  onMerge,
  onRefresh,
  onResolve,
  resolvingConflictId,
  total,
}: {
  conflicts: MemoryConflict[]
  error: string | null
  loading: boolean
  onMerge: (conflict: MemoryConflict) => void
  onRefresh: () => void
  onResolve: (conflict: MemoryConflict, resolution: "keep_existing" | "replace") => void
  resolvingConflictId: string | null
  total: number
}) {
  if (!loading && !error && total === 0) return null

  return (
    <section className="memory-conflict-queue" aria-label="Memory conflict review queue">
      <div className="memory-conflict-header">
        <div className="memory-conflict-title">
          <ShieldAlert className="size-4" />
          <div>
            <h3>Needs Review</h3>
            <p>
              {total} memory conflict{total === 1 ? "" : "s"} waiting for a human decision.
            </p>
          </div>
        </div>
        <button disabled={loading} onClick={onRefresh} type="button">
          <RefreshCw className={cn("size-3.5", loading && "animate-spin")} />
          Refresh
        </button>
      </div>

      {error ? <div className="memory-error">{error}</div> : null}
      {loading && conflicts.length === 0 ? (
        <div className="memory-loading">
          <span />
          Loading review queue
        </div>
      ) : null}
      <div className="memory-conflict-list">
        {conflicts.map((conflict, index) => (
          <ConflictCard
            conflict={conflict}
            key={conflict.id}
            onMerge={() => onMerge(conflict)}
            onResolve={(resolution) => onResolve(conflict, resolution)}
            order={index}
            resolving={resolvingConflictId === conflict.id}
          />
        ))}
      </div>
    </section>
  )
}

function MemoryWriteReviewQueue({
  error,
  events,
  loading,
  onRefresh,
  onResolve,
  resolvingEventId,
  total,
}: {
  error: string | null
  events: MemoryWriteEvent[]
  loading: boolean
  onRefresh: () => void
  onResolve: (event: MemoryWriteEvent, action: "approve" | "undo") => void
  resolvingEventId: string | null
  total: number
}) {
  if (!loading && !error && total === 0) return null

  return (
    <section className="memory-write-review-queue" aria-label="Memory write review queue">
      <div className="memory-conflict-header">
        <div className="memory-conflict-title">
          <Brain className="size-4" />
          <div>
            <h3>Write Review</h3>
            <p>
              {total} memory write{total === 1 ? "" : "s"} waiting for approval.
            </p>
          </div>
        </div>
        <button disabled={loading} onClick={onRefresh} type="button">
          <RefreshCw className={cn("size-3.5", loading && "animate-spin")} />
          Refresh
        </button>
      </div>

      {error ? <div className="memory-error">{error}</div> : null}
      {loading && events.length === 0 ? (
        <div className="memory-loading">
          <span />
          Loading write review
        </div>
      ) : null}
      <div className="memory-write-event-list">
        {events.map((event, index) => (
          <MemoryWriteEventCard
            event={event}
            key={event.id}
            onResolve={(action) => onResolve(event, action)}
            order={index}
            resolving={resolvingEventId === event.id}
          />
        ))}
      </div>
    </section>
  )
}

function MemoryWriteEventCard({
  event,
  onResolve,
  order,
  resolving,
}: {
  event: MemoryWriteEvent
  onResolve: (action: "approve" | "undo") => void
  order: number
  resolving: boolean
}) {
  return (
    <motion.article
      animate={{ opacity: 1, y: 0 }}
      className="memory-write-event-card"
      initial={{ opacity: 0, y: 8 }}
      transition={{ delay: Math.min(order * 0.03, 0.18), duration: 0.18 }}
    >
      <div className="memory-conflict-meta">
        <span>{event.write_type.replace(/_/g, " ")}</span>
        <span>{event.sensitivity || "normal"}</span>
        <span>{formatMemoryDate(event.created_at)}</span>
      </div>
      <p>{event.user_visible_text}</p>
      {event.source_excerpt ? <small>{event.source_excerpt}</small> : null}
      <div className="memory-conflict-actions">
        <button disabled={resolving} onClick={() => onResolve("approve")} type="button">
          <Check className="size-3.5" />
          Approve
        </button>
        <button disabled={resolving} onClick={() => onResolve("undo")} type="button">
          <Archive className="size-3.5" />
          Undo write
        </button>
      </div>
    </motion.article>
  )
}

function ConflictCard({
  conflict,
  onMerge,
  onResolve,
  order,
  resolving,
}: {
  conflict: MemoryConflict
  onMerge: () => void
  onResolve: (resolution: "keep_existing" | "replace") => void
  order: number
  resolving: boolean
}) {
  const existingContent = conflict.existing_content || "Existing memory is missing."
  const similarity = Math.round((conflict.similarity || 0) * 100)

  return (
    <motion.article
      animate={{ opacity: 1, y: 0 }}
      className="memory-conflict-card"
      initial={{ opacity: 0, y: 8 }}
      transition={{ delay: Math.min(order * 0.03, 0.18), duration: 0.18 }}
    >
      <div className="memory-conflict-meta">
        <span>{formatConflictType(conflict.conflict_type)}</span>
        <span>{similarity}% similar</span>
        <span>{formatMemoryDate(conflict.created_at)}</span>
      </div>
      <p className="memory-conflict-reason">{conflict.reason || "The proposed memory contradicts an active memory."}</p>
      <div className="memory-conflict-compare">
        <ConflictTextBlock label="Current memory" text={existingContent} />
        <ConflictTextBlock label="Proposed memory" text={conflict.proposed_content} />
      </div>
      <div className="memory-conflict-actions">
        <button disabled={resolving} onClick={() => onResolve("keep_existing")} type="button">
          <Check className="size-3.5" />
          Keep current
        </button>
        <button disabled={resolving} onClick={() => onResolve("replace")} type="button">
          <RefreshCw className="size-3.5" />
          Use proposed
        </button>
        <button disabled={resolving} onClick={onMerge} type="button">
          <GitMerge className="size-3.5" />
          Merge
        </button>
      </div>
    </motion.article>
  )
}

function ConflictTextBlock({ label, text }: { label: string; text: string }) {
  return (
    <div className="memory-conflict-text">
      <span>{label}</span>
      <p>{text}</p>
    </div>
  )
}

function MemoryCard({
  memory,
  onArchive,
  onDelete,
  onEdit,
  onInspect,
  order,
}: {
  memory: MemoryItem
  onArchive: () => void
  onDelete: () => void
  onEdit: () => void
  onInspect: () => void
  order: number
}) {
  const content = memory.content || memory.name || ""
  const codeMatch = content.match(/```[\w]*\n([\s\S]*?)```/)
  const snippet = codeMatch ? codeMatch[1].trim() : null
  const displayContent = codeMatch ? content.replace(codeMatch[0], "").trim() : content

  return (
    <motion.div
      animate={{ opacity: 1, y: 0 }}
      className="memory-card"
      initial={{ opacity: 0, y: 8 }}
      transition={{ delay: Math.min(order * 0.025, 0.16), duration: 0.18 }}
    >
      <div className="memory-card-meta">
        <div className="memory-card-left">
          <TypeBadge type={memory.type} />
          <ConfidenceDot confidence={memory.confidence} />
        </div>
        <span>{formatMemoryDate(memory.updated_at || memory.created_at)}</span>
      </div>
      {displayContent ? <p className="memory-card-content">{displayContent}</p> : null}
      {snippet ? (
        <div className="memory-card-preview">
          <code>{snippet}</code>
        </div>
      ) : null}
      <div className="memory-card-actions">
        <button onClick={onInspect} type="button">
          <Eye className="size-3.5" />
          Inspect
        </button>
        <button onClick={onEdit} type="button">
          <Edit3 className="size-3.5" />
          Edit
        </button>
        {memory.status !== "archived" ? (
          <button onClick={onArchive} type="button">
            <Archive className="size-3.5" />
            Archive
          </button>
        ) : null}
        <button onClick={onDelete} type="button">
          <Trash2 className="size-3.5" />
          Delete
        </button>
      </div>
    </motion.div>
  )
}

function MemoryDetailModal({ memory, onClose }: { memory: MemoryItem; onClose: () => void }) {
  const events = memory.events ?? []
  return (
    <MemoryModalFrame onClose={onClose} title="Memory Detail" wide>
      <div className="memory-detail-grid">
        <DetailItem label="Type" value={memory.type} />
        <DetailItem label="Status" value={memory.status} />
        <DetailItem label="Scope" value={memory.scope || "global"} />
        <DetailItem label="Confidence" value={`${Math.round(memory.confidence * 100)}%`} />
        <DetailItem label="Source" value={memory.source_type || "unknown"} />
        <DetailItem label="Session" value={memory.source_session_id || "none"} />
        <DetailItem label="Captured" value={formatMemoryDate(memory.captured_at || null)} />
        <DetailItem label="Updated" value={formatMemoryDate(memory.updated_at || memory.created_at)} />
      </div>
      <div className="memory-detail-section">
        <span>Content</span>
        <p>{memory.content || memory.name}</p>
      </div>
      <div className="memory-detail-section">
        <span>Storage</span>
        <code>{memory.path}</code>
      </div>
      <div className="memory-detail-section">
        <span>Events</span>
        {events.length ? (
          <div className="memory-event-list">
            {events.map((event) => (
              <div className="memory-event-row" key={event.id}>
                <strong>{event.event_type}</strong>
                <span>{formatMemoryDate(event.created_at)}</span>
                <code>{safeJson(event.payload)}</code>
              </div>
            ))}
          </div>
        ) : (
          <p>No event history recorded.</p>
        )}
      </div>
    </MemoryModalFrame>
  )
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="memory-detail-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function TypeBadge({ type }: { type: string }) {
  return <span className={cn("memory-type-badge", `type-${type}`)}>{type}</span>
}

function ConfidenceDot({ confidence }: { confidence: number }) {
  return (
    <span
      aria-label={`Confidence ${Math.round(confidence * 100)} percent`}
      className={cn(
        "confidence-dot",
        confidence >= 0.8 && "high",
        confidence >= 0.5 && confidence < 0.8 && "medium",
        confidence < 0.5 && "low",
      )}
    />
  )
}

function AddMemoryModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [content, setContent] = useState("")
  const [type, setType] = useState("user")
  const [scope, setScope] = useState("")
  const [saving, setSaving] = useState(false)

  async function handleSave() {
    if (!content.trim()) return
    setSaving(true)
    try {
      await addMemory(content.trim(), type, scope.trim() || undefined)
      onSaved()
    } finally {
      setSaving(false)
    }
  }

  return (
    <MemoryModalFrame onClose={onClose} title="Add Memory">
      <textarea
        autoFocus
        className="memory-modal-textarea"
        onChange={(event) => setContent(event.target.value)}
        placeholder="What should Geneva remember?"
        rows={5}
        value={content}
      />
      <div className="memory-modal-grid">
        <label>
          <span>Type</span>
          <select onChange={(event) => setType(event.target.value)} value={type}>
            {MEMORY_TYPES.filter((item) => item !== "all").map((item) => (
              <option key={item} value={item}>
                {titleCase(item)}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Scope</span>
          <input
            onChange={(event) => setScope(event.target.value)}
            placeholder="project scope"
            value={scope}
          />
        </label>
      </div>
      <div className="memory-modal-actions">
        <Button onClick={onClose} type="button" variant="quiet">
          Cancel
        </Button>
        <Button disabled={!content.trim() || saving} onClick={() => void handleSave()} type="button">
          {saving ? "Saving..." : "Save"}
        </Button>
      </div>
    </MemoryModalFrame>
  )
}

function EditMemoryModal({
  memory,
  onClose,
  onSaved,
}: {
  memory: MemoryItem
  onClose: () => void
  onSaved: () => void
}) {
  const [content, setContent] = useState(memory.content)
  const [saving, setSaving] = useState(false)

  async function handleSave() {
    if (!content.trim()) return
    setSaving(true)
    try {
      await updateMemory(memory.id, content.trim())
      onSaved()
    } finally {
      setSaving(false)
    }
  }

  return (
    <MemoryModalFrame onClose={onClose} title="Edit Memory">
      <textarea
        autoFocus
        className="memory-modal-textarea"
        onChange={(event) => setContent(event.target.value)}
        rows={5}
        value={content}
      />
      <div className="memory-edit-meta">
        <TypeBadge type={memory.type} />
        {memory.scope ? <span>{memory.scope}</span> : null}
      </div>
      <div className="memory-modal-actions">
        <Button onClick={onClose} type="button" variant="quiet">
          Cancel
        </Button>
        <Button disabled={!content.trim() || saving} onClick={() => void handleSave()} type="button">
          {saving ? "Saving..." : "Save"}
        </Button>
      </div>
    </MemoryModalFrame>
  )
}

function MergeConflictModal({
  conflict,
  onClose,
  onResolve,
  resolving,
}: {
  conflict: MemoryConflict
  onClose: () => void
  onResolve: (mergedContent: string) => void
  resolving: boolean
}) {
  const [mergedContent, setMergedContent] = useState(defaultMergedContent(conflict))

  return (
    <MemoryModalFrame onClose={onClose} title="Merge Memory Conflict" wide>
      <div className="memory-conflict-modal-grid">
        <ConflictTextBlock label="Current memory" text={conflict.existing_content || "Missing current memory."} />
        <ConflictTextBlock label="Proposed memory" text={conflict.proposed_content} />
      </div>
      <label className="memory-merge-label">
        <span>Resolved memory</span>
        <textarea
          autoFocus
          className="memory-modal-textarea"
          onChange={(event) => setMergedContent(event.target.value)}
          rows={7}
          value={mergedContent}
        />
      </label>
      <div className="memory-modal-actions">
        <Button onClick={onClose} type="button" variant="quiet">
          Cancel
        </Button>
        <Button
          disabled={!mergedContent.trim() || resolving}
          onClick={() => onResolve(mergedContent.trim())}
          type="button"
        >
          {resolving ? "Resolving..." : "Save merged memory"}
        </Button>
      </div>
    </MemoryModalFrame>
  )
}

function MemoryModalFrame({
  children,
  onClose,
  title,
  wide = false,
}: {
  children: ReactNode
  onClose: () => void
  title: string
  wide?: boolean
}) {
  return (
    <div className="memory-modal-backdrop">
      <motion.div
        animate={{ opacity: 1, y: 0 }}
        className={cn("memory-modal", wide && "memory-modal-wide")}
        initial={{ opacity: 0, y: 12 }}
        transition={{ duration: 0.18 }}
      >
        <div className="memory-modal-header">
          <div className="memory-modal-title">
            <Brain className="size-4" />
            <h3>{title}</h3>
          </div>
          <button aria-label="Close" onClick={onClose} type="button">
            <X className="size-4" />
          </button>
        </div>
        {children}
      </motion.div>
    </div>
  )
}

function safeJson(value: unknown): string {
  if (value === null || value === undefined) return "{}"
  if (typeof value === "string") return value
  try {
    return JSON.stringify(value)
  } catch {
    return String(value)
  }
}

function LoadingSpinner() {
  return (
    <div className="memory-loading">
      <span />
      Loading memories
    </div>
  )
}

function EmptyMemoryState() {
  return (
    <div className="memory-empty">
      <Brain className="size-5" />
      <span>No memories found</span>
    </div>
  )
}

function titleCase(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1)
}

function formatConflictType(value: string): string {
  if (!value) return "Conflict"
  return value
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map(titleCase)
    .join(" ")
}

function formatCount(value: number, label: string): string {
  return `${value} ${label}${value === 1 ? "" : "s"}`
}

function defaultMergedContent(conflict: MemoryConflict): string {
  const type = conflict.conflict_type.toLowerCase()
  if (type.includes("polarity") || type.includes("correction")) {
    return conflict.proposed_content
  }
  return [conflict.existing_content, conflict.proposed_content].filter(Boolean).join("\n\n")
}

function formatMemoryDate(value: string | null): string {
  if (!value) return ""
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value.slice(0, 10)
  const diffMs = Date.now() - date.getTime()
  const days = Math.floor(diffMs / 86_400_000)
  if (days <= 0) return "today"
  if (days < 7) return `${days} day${days === 1 ? "" : "s"} ago`
  return date.toLocaleDateString(void 0, { month: "short", day: "numeric" })
}
