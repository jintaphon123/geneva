import { type ReactNode, useEffect, useState } from "react"
import { AlertTriangle, Brain, CheckCircle2, ChevronDown, ChevronUp, Clock3, LoaderCircle, OctagonX, Wrench } from "lucide-react"

import { GenevaMark } from "@/components/GenevaMark"
import { cn } from "@/lib/utils"
import type { ActivityEvent, ChatMessage, ToolTraceEvent } from "@/types"

export function ActivityPanel({
  error,
  events,
  hideLiveThinking = false,
  loading,
}: {
  error: string | null
  events: ActivityEvent[]
  hideLiveThinking?: boolean
  loading: boolean
}) {
  const hasActive = loading && events.some((event) => ["queued", "running", "waiting"].includes(event.status))
  const hasProblem = Boolean(error) || events.some((event) => ["error", "timeout", "limit"].includes(event.status))
  const thinkingEvent = hideLiveThinking ? undefined : activityThinkingEvent(events, loading, hasProblem)
  const visibleEvents = compactActivityEvents(events)
  const current = getCurrentActivityEvent(events, loading)
  const [expanded, setExpanded] = useState(() => hasProblem)

  useEffect(() => {
    if (hasProblem) setExpanded(true)
  }, [hasProblem])

  if (thinkingEvent) {
    return (
      <div className="activity-panel activity-thinking-panel is-live">
        <div aria-label={activityThinkingLabel(thinkingEvent)} className="activity-thinking-row" role="status">
          <GenevaMark className="activity-geneva-mark" state="thinking" variant="loader" />
          <span className="activity-thinking-label">{activityThinkingLabel(thinkingEvent)}</span>
        </div>
      </div>
    )
  }

  if (!expanded && !hasProblem && loading && !thinkingEvent) return null
  if (!visibleEvents.length && !loading && !hasProblem) return null

  return (
    <div className={cn("activity-panel", expanded && "open", loading && "is-live", hasProblem && "has-problem")}>
      <button
        aria-expanded={expanded}
        className="activity-summary"
        onClick={() => setExpanded((value) => !value)}
        type="button"
      >
        <GenevaMark
          className="activity-geneva-mark"
          state={hasProblem ? "error" : loading ? "thinking" : "idle"}
          variant="loader"
        />
        <span className="activity-copy">
          <span className="activity-title">{current ? formatActivityTitle(current) : "Activity"}</span>
          {current ? <ActivityDetail event={current} /> : null}
          {hasActive ? <span className="activity-cursor blinking" /> : null}
        </span>
        <div className="activity-summary-spacer" />
        {expanded ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
      </button>
      {expanded ? (
        <div className="activity-list">
          {visibleEvents.map((event) => (
            <div className={cn("activity-item", `status-${event.status}`)} key={event.id}>
              <span className="activity-item-icon">{activityIcon(event, loading)}</span>
              <div className="activity-item-main">
                <div className="activity-item-head">
                  <span className="activity-item-title">{formatActivityTitle(event)}</span>
                  <span className="activity-item-status">{formatActivityStatus(event, loading)}</span>
                  {event.durationMs != null ? (
                    <span className="activity-item-duration">{formatDuration(event.durationMs)}</span>
                  ) : null}
                </div>
                <ActivityDetail event={event} variant="block" />
                {event.error && event.error !== event.detail ? (
                  <div className="activity-item-error">{event.error}</div>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}

function ActivityDetail({ event, variant = "inline" }: { event: ActivityEvent; variant?: "inline" | "block" }) {
  const detail = formatActivityDetail(event)
  if (!detail) return null
  if (variant === "block") return <div className="activity-item-detail">{detail}</div>
  return <span className="activity-detail">{detail}</span>
}

export function activityEventsForMessage(message: ChatMessage): ActivityEvent[] {
  if (message.activityEvents?.length) return message.activityEvents
  return toolTraceToActivityEvents(message.toolEvents ?? [])
}

export function hasLiveThinkingEvent(events: ActivityEvent[], loading: boolean): boolean {
  return Boolean(activityThinkingEvent(events, loading, false))
}

function toolTraceToActivityEvents(events: ToolTraceEvent[]): ActivityEvent[] {
  return events.map((toolTrace) => ({
    id: toolTrace.id,
    kind: toolTrace.toolName === "AgentLoop" ? "thinking" : "tool",
    title:
      toolTrace.status === "complete"
        ? `Finished ${formatToolLabel(toolTrace.toolName)}`
        : toolTrace.status === "timeout"
          ? `${formatToolLabel(toolTrace.toolName)} timed out`
          : toolTrace.status === "error"
            ? `${formatToolLabel(toolTrace.toolName)} failed`
            : toolTrace.status === "limit"
              ? "Reached tool turn limit"
              : `Using ${formatToolLabel(toolTrace.toolName)}`,
    detail: toolTrace.summary || toolTrace.inputPreview,
    status: toolTrace.status,
    durationMs: toolTrace.durationMs,
    timeoutSeconds: toolTrace.timeoutSeconds,
    toolName: toolTrace.toolName,
    error: toolTrace.error,
  }))
}

function compactActivityEvents(events: ActivityEvent[]): ActivityEvent[] {
  const nonEmpty = events.filter((event) => event.title.trim())
  const latestById = new Map<string, ActivityEvent>()
  for (const event of nonEmpty) latestById.set(event.id, event)
  
  return Array.from(latestById.values())
    .filter((event) => {
      // Hide completed AgentLoop or generic "working" steps, as it's weird to show a checkmark for them
      if (event.kind === "heartbeat") return false
      if (event.status === "complete" && (event.toolName === "AgentLoop" || event.title.toLowerCase().includes("working"))) {
        return false
      }
      return true
    })
    .slice(-8)
}

function getCurrentActivityEvent(events: ActivityEvent[], loading: boolean): ActivityEvent | undefined {
  const running = [...events].reverse().find((event) => ["running", "waiting", "queued"].includes(event.status))
  if (running && loading) return running
  const problem = [...events].reverse().find((event) => ["error", "timeout", "limit"].includes(event.status))
  if (problem) return problem
  return [...events].reverse().find((event) => event.status === "complete") ?? events.at(-1)
}

function formatActivityTitle(event: ActivityEvent): string {
  if (event.kind === "tool" && event.toolName) {
    const label = formatToolLabel(event.toolName)
    if (event.status === "complete") return `Finished ${label}`
    if (event.status === "timeout") return `${label} timed out`
    if (event.status === "error") return `${label} failed`
    if (event.status === "limit") return "Reached tool limit"
    return `Using ${label}`
  }
  if (event.kind === "permission" && event.toolName) {
    return event.status === "waiting" ? `Waiting for ${formatToolLabel(event.toolName)} approval` : event.title
  }
  return event.title
}

function activityThinkingEvent(
  events: ActivityEvent[],
  loading: boolean,
  hasProblem: boolean,
): ActivityEvent | undefined {
  if (!loading || hasProblem) return undefined
  return [...events].reverse().find((event) => event.kind === "thinking" && ["queued", "running", "waiting"].includes(event.status))
}

function activityThinkingLabel(event: ActivityEvent): string {
  const title = formatActivityTitle(event).trim()
  if (!title || title.toLowerCase() === "thinking") return "Thinking"
  return title
}

function formatActivityDetail(event: ActivityEvent): string | null {
  const detail = event.detail?.trim()
  if (!detail) return null
  const toolLabel = event.toolName ? formatToolLabel(event.toolName) : null
  const normalized = toolLabel ? detail.replaceAll(event.toolName ?? "", toolLabel) : detail
  if (/^\{[\s\S]*\}$/.test(normalized) || normalized.includes('\\"')) {
    return event.kind === "tool" ? "Input preview captured" : null
  }
  return normalized
}

function activityIcon(event: ActivityEvent, loading = true): ReactNode {
  const isRunning = event.status === "running" || event.status === "queued"
  const wasStopped = isRunning && !loading

  if (wasStopped) return <OctagonX className="size-3.5 text-rose-500" />
  if (event.status === "error" || event.status === "timeout" || event.status === "limit") {
    return <AlertTriangle className="size-3.5" />
  }
  if (event.status === "complete") return <CheckCircle2 className="size-3.5" />
  if (event.status === "waiting") return <Clock3 className="size-3.5" />
  if (event.kind === "memory" || event.kind === "memory_update") return <Brain className={cn("size-3.5", isRunning && "animate-pulse")} />
  if (event.kind === "tool") return <Wrench className={cn("size-3.5", isRunning && "animate-spin")} />
  return <LoaderCircle className={cn("size-3.5", isRunning ? "animate-spin" : "")} />
}

function formatToolLabel(toolName: string | null | undefined): string {
  const raw = String(toolName ?? "").trim()
  if (!raw) return "Tool"
  const known: Record<string, string> = {
    AgentLoop: "Agent loop",
    BashCommand: "Run command",
    ListMcpResourcesTool: "List MCP resources",
    ReadFileTool: "Read file",
    ReadMcpResourceTool: "Read MCP resource",
    ToolSearch: "Find tool",
    WebFetch: "Read page",
    WebSearch: "Search web",
    WriteFileTool: "Edit file",
  }
  if (known[raw]) return known[raw]
  return raw
    .replace(/Tool$/, "")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .trim()
}

function formatActivityStatus(event: ActivityEvent, loading = true): string {
  const isRunning = event.status === "running" || event.status === "queued"
  if (isRunning && !loading) return "stopped"
  if (event.status === "timeout") return `timeout${event.timeoutSeconds ? ` after ${event.timeoutSeconds}s` : ""}`
  if (event.status === "error") return "failed"
  if (event.status === "complete") return "complete"
  if (event.status === "limit") return "limit"
  if (event.status === "waiting") return "waiting"
  if (event.status === "queued") return "queued"
  return "running"
}

function formatDuration(durationMs: number): string {
  if (durationMs < 1000) return `${durationMs}ms`
  return `${(durationMs / 1000).toFixed(durationMs < 10_000 ? 1 : 0)}s`
}
