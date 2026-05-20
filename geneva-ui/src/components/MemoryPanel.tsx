import { Brain, Clock3, DatabaseZap, FolderKanban, Gauge, ShieldAlert, X } from "lucide-react"
import { motion } from "framer-motion"
import { type ReactNode, useEffect, useState } from "react"

import { ContextLedgerCard } from "@/components/ContextLedgerCard"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { fetchContextLedger, fetchMemoryBrowserStats, listMemories } from "@/lib/api"
import { cn } from "@/lib/utils"
import type { ContextLedgerPayload, MemoryItem, MemoryStats, Project } from "@/types"

type MemoryPanelProps = {
  stats: MemoryStats
  sessionId?: string | null
  activeProject?: Project | null
  onClose: () => void
}

export function MemoryPanel({ activeProject, sessionId, stats, onClose }: MemoryPanelProps) {
  const memories = stats.recent.slice(0, 5)
  const [contextLedger, setContextLedger] = useState<ContextLedgerPayload | null>(null)
  const [contextLedgerError, setContextLedgerError] = useState<string | null>(null)
  const [projectMemories, setProjectMemories] = useState<MemoryItem[]>([])
  const [projectMemoryError, setProjectMemoryError] = useState<string | null>(null)
  const [openConflicts, setOpenConflicts] = useState(0)

  useEffect(() => {
    let cancelled = false
    void fetchMemoryBrowserStats()
      .then((browserStats) => {
        if (!cancelled) setOpenConflicts(browserStats.conflicts_by_status?.open ?? 0)
      })
      .catch(() => {
        if (!cancelled) setOpenConflicts(0)
      })
    return () => {
      cancelled = true
    }
  }, [stats.active, stats.superseded, stats.expired])

  useEffect(() => {
    let cancelled = false
    void fetchContextLedger(sessionId, 20)
      .then((payload) => {
        if (!cancelled) {
          setContextLedger(payload)
          setContextLedgerError(null)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setContextLedger(null)
          setContextLedgerError("Could not load context ledger")
        }
      })
    return () => {
      cancelled = true
    }
  }, [sessionId, stats.lastIndexed, stats.active])

  useEffect(() => {
    if (!activeProject) {
      setProjectMemories([])
      setProjectMemoryError(null)
      return
    }
    let cancelled = false
    void listMemories({
      scope: activeProject.id,
      status: "active",
      limit: 6,
      offset: 0,
    })
      .then((result) => {
        if (!cancelled) setProjectMemories(result.items)
      })
      .catch(() => {
        if (!cancelled) {
          setProjectMemories([])
          setProjectMemoryError("Could not load project memories")
        }
      })
    return () => {
      cancelled = true
    }
  }, [activeProject])

  return (
    <aside className="memory-rail" aria-label="Context and memory">
      <header className="memory-rail-header">
        <div className="memory-rail-title-block">
          <div className="memory-rail-icon">
            <DatabaseZap className="size-4" />
          </div>
          <div>
            <div className="memory-rail-kicker">Geneva</div>
            <h2>Context + Memory</h2>
          </div>
        </div>
        <Button aria-label="Hide memory" onClick={onClose} size="compactIcon" variant="quiet">
          <X className="size-4" />
        </Button>
      </header>

      <div className="memory-rail-status">
        <Clock3 className="size-3.5" />
        <span>{stats.lastIndexed ? `Indexed ${formatRelative(stats.lastIndexed)}` : "Not indexed yet"}</span>
      </div>

      <div className="memory-stat-grid">
        <StatPill label="Active" value={stats.active} />
        <StatPill label="Superseded" value={stats.superseded} />
        <StatPill label="Expired" value={stats.expired} />
        <StatPill label="Review" value={openConflicts} tone={openConflicts > 0 ? "warning" : "default"} />
      </div>

      <ScrollArea className="memory-rail-scroll">
        <section className="memory-rail-section">
          <SectionHeading
            icon={<Gauge className="size-3.5" />}
            label="Context budget"
            text="What entered the model, what was trimmed, and why."
          />
          <ContextLedgerCard error={contextLedgerError} payload={contextLedger} />
        </section>

        {openConflicts > 0 ? (
          <section className="memory-rail-section">
            <div className="memory-review-callout">
              <ShieldAlert className="size-4" />
              <div>
                <strong>{openConflicts} memory conflict{openConflicts === 1 ? "" : "s"}</strong>
                <span>Review queue needs a human decision before those memories become trusted.</span>
              </div>
            </div>
          </section>
        ) : null}

        {activeProject ? (
          <section className="memory-rail-section">
            <SectionHeading
              icon={<FolderKanban className="size-3.5" />}
              label={`${activeProject.name} memories`}
              text="Project-scoped facts stay separated from global preferences."
            />
            <MemoryList
              emptyText="No project memories yet. Capture decisions, sources, and formulas from this project."
              memories={projectMemories}
            />
            {projectMemoryError ? (
              <div className="mt-2 text-[12px] text-destructive">{projectMemoryError}</div>
            ) : null}
          </section>
        ) : null}
        <section className="memory-rail-section">
          <SectionHeading
            icon={<Brain className="size-3.5" />}
            label="Recent memories"
            text="Latest active memories available to future turns."
          />
          <MemoryList
            emptyText="New memories will appear here after a chat turn finishes."
            memories={memories}
          />
        </section>
      </ScrollArea>
    </aside>
  )
}

function SectionHeading({
  icon,
  label,
  text,
}: {
  icon: ReactNode
  label: string
  text: string
}) {
  return (
    <div className="memory-section-heading">
      <div>
        {icon}
        <span>{label}</span>
      </div>
      <p>{text}</p>
    </div>
  )
}

function MemoryList({ emptyText, memories }: { emptyText: string; memories: MemoryItem[] }) {
  return (
        <div className="memory-rail-list">
          {memories.map((memory, index) => (
            <motion.div
              animate={{ opacity: 1, y: 0 }}
              className="memory-rail-card"
              initial={{ opacity: 0, y: 8 }}
              key={memory.id ?? `${memory.content}-${index}`}
              transition={{ delay: index * 0.025, duration: 0.16 }}
            >
              <div className="memory-rail-card-meta">
                <TypeChip type={memory.type} />
                <span>
                  {memory.updated_at ? formatRelative(memory.updated_at) : ""}
                </span>
              </div>
              <div className="memory-rail-card-copy">
                {memory.content || memory.name || "Memory item"}
              </div>
            </motion.div>
          ))}
          {!memories.length ? (
            <div className="memory-rail-empty">
              {emptyText}
            </div>
          ) : null}
        </div>
  )
}

function StatPill({
  label,
  tone = "default",
  value,
}: {
  label: string
  tone?: "default" | "warning"
  value: number
}) {
  return (
    <div
      className={cn(
        "rounded-[10px] border border-border/75 bg-card/78 px-2.5 py-2",
        tone === "warning" && "border-amber-500/35 bg-amber-500/10",
      )}
    >
      <div className="text-[17px] font-semibold leading-none text-foreground">{value}</div>
      <div className="mt-1 truncate text-[11px] text-muted-foreground">{label}</div>
    </div>
  )
}

function TypeChip({ type }: { type?: MemoryItem["type"] }) {
  const label = type || "memory"
  return (
    <span
      className={cn(
        "rounded-full px-2 py-0.5 text-[11px] font-medium",
        label === "feedback" && "bg-primary/10 text-primary",
        label === "project" && "bg-emerald-500/10 text-emerald-700",
        label === "reference" && "bg-blue-500/10 text-blue-700",
        label === "user" && "bg-zinc-500/10 text-zinc-700",
        !["feedback", "project", "reference", "user"].includes(label) &&
          "bg-muted text-muted-foreground",
      )}
    >
      {label}
    </span>
  )
}

function formatRelative(value: string): string {
  const timestamp = new Date(value).getTime()
  if (Number.isNaN(timestamp)) return value

  const diffMs = Date.now() - timestamp
  const minutes = Math.max(0, Math.floor(diffMs / 60000))
  if (minutes < 1) return "just now"
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} hr ago`
  const days = Math.floor(hours / 24)
  return `${days} day${days > 1 ? "s" : ""} ago`
}
