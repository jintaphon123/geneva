import type { ActivityEvent, StreamPayload, ToolTraceEvent } from "@/types"

export function traceFromStreamEvent(event: StreamPayload): ToolTraceEvent | null {
  if (
    event.type !== "tool_call_start" &&
    event.type !== "tool_executing" &&
    event.type !== "tool_complete" &&
    event.type !== "tool_error" &&
    event.type !== "tool_timeout" &&
    event.type !== "agent_loop_limit"
  ) {
    return null
  }
  const data = event.data ?? {}
  const toolName = String(data.tool_name ?? (event.type === "agent_loop_limit" ? "AgentLoop" : "Tool"))
  const status =
    event.type === "tool_timeout"
      ? "timeout"
      : event.type === "tool_error"
        ? "error"
        : event.type === "tool_complete"
          ? "complete"
          : event.type === "agent_loop_limit"
            ? "limit"
            : "running"
  const toolCallId = event.tool_call_id ?? (event.type === "agent_loop_limit" ? "agent-loop-limit" : null)
  return {
    id: toolCallId || `${event.turn_id || "turn"}-${event.event_seq ?? Date.now()}-${toolName}`,
    toolCallId,
    toolName,
    status,
    summary: typeof data.summary === "string" ? data.summary : undefined,
    inputPreview: typeof data.tool_input_preview === "string" ? data.tool_input_preview : undefined,
    outputPreview: typeof data.tool_output_preview === "string" ? data.tool_output_preview : undefined,
    error: event.error?.message || (typeof data.error === "string" ? data.error : null),
    durationMs: typeof data.duration_ms === "number" ? data.duration_ms : null,
    timeoutSeconds: typeof data.timeout_seconds === "number" ? data.timeout_seconds : null,
    turnIndex: typeof data.turn_index === "number" ? data.turn_index : null,
  }
}

export function mergeToolTrace(events: ToolTraceEvent[] | undefined, next: ToolTraceEvent): ToolTraceEvent[] {
  const current = events ?? []
  const index = current.findIndex((event) =>
    next.toolCallId ? event.toolCallId === next.toolCallId : event.id === next.id,
  )
  if (index === -1) return [...current, next]
  return current.map((event, eventIndex) =>
    eventIndex === index
      ? {
          ...event,
          ...next,
          id: event.id,
          summary: next.summary ?? event.summary,
          inputPreview: next.inputPreview ?? event.inputPreview,
          outputPreview: next.outputPreview ?? event.outputPreview,
          error: next.error ?? event.error,
          durationMs: next.durationMs ?? event.durationMs,
          timeoutSeconds: next.timeoutSeconds ?? event.timeoutSeconds,
          turnIndex: next.turnIndex ?? event.turnIndex,
        }
      : event,
  )
}

export function activityFromStreamEvent(event: StreamPayload, assistantId: string): ActivityEvent | null {
  const data = event.data ?? {}
  const turnId = event.turn_id || assistantId
  const timestamp = typeof event.timestamp === "number" ? event.timestamp : Date.now() / 1000

  if (event.type === "memory_load_start") {
    return {
      id: `${turnId}-memory`,
      kind: "memory",
      title: "Reading memory",
      detail: "Loading relevant long-term context",
      status: "running",
      timestamp,
    }
  }

  if (event.type === "memory_load_complete") {
    const chars = typeof data.chars === "number" ? data.chars : null
    const stats = data.stats && typeof data.stats === "object" ? (data.stats as Record<string, unknown>) : {}
    const active = typeof stats.total_active === "number" ? stats.total_active : null
    const detail = [
      chars !== null ? `${compactNumber(chars)} chars` : null,
      active !== null ? `${compactNumber(active)} active memories` : null,
    ].filter(Boolean).join(" · ")
    return {
      id: `${turnId}-memory`,
      kind: "memory",
      title: "Memory ready",
      detail: detail || "Relevant context loaded",
      status: "complete",
      timestamp,
    }
  }

  if (event.type === "agent_turn_start") {
    const turnIndex =
      typeof data.turn_index === "number"
        ? data.turn_index
        : typeof data.turn === "number"
          ? data.turn
          : undefined
    return {
      id: `${turnId}-think-${turnIndex ?? event.event_seq ?? "1"}`,
      kind: "thinking",
      title: "Thinking",
      detail: "Planning the next step",
      status: "running",
      timestamp,
    }
  }

  if (event.type === "agent_turn_complete") {
    const turnIndex =
      typeof data.turn_index === "number"
        ? data.turn_index
        : typeof data.turn === "number"
          ? data.turn
          : undefined
    const output =
      data.tool_output && typeof data.tool_output === "object"
        ? (data.tool_output as Record<string, unknown>)
        : {}
    const toolCount = typeof output.tool_count === "number" ? output.tool_count : null
    const waitingForTools = data.status === "waiting_for_tools"
    return {
      id: `${turnId}-think-${turnIndex ?? event.event_seq ?? "1"}`,
      kind: "thinking",
      title: waitingForTools ? "Planned tool use" : "Thought through response",
      detail:
        typeof data.summary === "string"
          ? data.summary
          : toolCount !== null
            ? `${toolCount} tool call${toolCount === 1 ? "" : "s"}`
            : "No tools needed",
      status: "complete",
      timestamp,
    }
  }

  if (
    event.type === "tool_call_start" ||
    event.type === "tool_executing" ||
    event.type === "tool_complete" ||
    event.type === "tool_error" ||
    event.type === "tool_timeout" ||
    event.type === "agent_loop_limit"
  ) {
    const toolTrace = traceFromStreamEvent(event)
    if (!toolTrace) return null
    const title =
      toolTrace.status === "complete"
        ? `Finished ${toolTrace.toolName}`
        : toolTrace.status === "timeout"
          ? `${toolTrace.toolName} timed out`
          : toolTrace.status === "error"
            ? `${toolTrace.toolName} failed`
            : toolTrace.status === "limit"
              ? "Reached tool turn limit"
              : `Using ${toolTrace.toolName}`
    return {
      id: toolTrace.toolCallId || toolTrace.id,
      kind: toolTrace.toolName === "AgentLoop" ? "thinking" : "tool",
      title,
      detail: toolTrace.summary || toolTrace.inputPreview || undefined,
      status: toolTrace.status,
      timestamp,
      durationMs: toolTrace.durationMs,
      timeoutSeconds: toolTrace.timeoutSeconds,
      toolName: toolTrace.toolName,
      error: toolTrace.error,
    }
  }

  if (event.type === "tool_permission_request") {
    const requestId = String(data.request_id ?? event.event_seq ?? "permission")
    const toolName = String(data.tool_name ?? "Tool")
    return {
      id: `${turnId}-permission-${requestId}`,
      kind: "permission",
      title: `Waiting for ${toolName} approval`,
      detail: typeof data.message === "string" ? data.message : "This tool needs permission before it can run.",
      status: "waiting",
      timestamp,
      toolName,
    }
  }

  if (event.type === "tool_permission_resolved") {
    const requestId = String(data.request_id ?? event.event_seq ?? "permission")
    const approved = Boolean(data.approved)
    return {
      id: `${turnId}-permission-${requestId}`,
      kind: "permission",
      title: approved ? "Tool approved" : "Tool denied",
      detail: approved ? "Continuing the run" : "Continuing without that tool",
      status: "complete",
      timestamp,
    }
  }

  if (event.type === "memory_update") {
    const action = typeof data.action === "string" ? data.action : "NOOP"
    return {
      id: `${turnId}-memory-update`,
      kind: "memory_update",
      title: action === "NOOP" ? "Memory checked" : "Memory updated",
      detail: typeof data.title === "string" ? `${data.title} · ${action}` : action,
      status: "complete",
      timestamp,
    }
  }

  if (event.type === "heartbeat") {
    return {
      id: `${turnId}-heartbeat`,
      kind: "heartbeat",
      title: "Still working",
      detail: "The model is still processing this turn",
      status: "running",
      timestamp,
    }
  }

  if (event.type === "error") {
    return {
      id: `${turnId}-error`,
      kind: "error",
      title: "Run interrupted",
      detail: event.error?.message || "Geneva hit an unexpected problem.",
      status: "error",
      timestamp,
      error: event.error?.message || null,
    }
  }

  if (event.type === "turn_complete") {
    return {
      id: `${turnId}-complete`,
      kind: "complete",
      title: "Response complete",
      detail: "Ready",
      status: "complete",
      timestamp,
    }
  }

  return null
}

export function mergeActivityEvent(events: ActivityEvent[] | undefined, next: ActivityEvent): ActivityEvent[] {
  const current = events ?? []
  const index = current.findIndex((event) => event.id === next.id)
  if (index === -1) return [...current, next]
  return current.map((event, eventIndex) =>
    eventIndex === index
      ? {
          ...event,
          ...next,
          detail: next.detail ?? event.detail,
          durationMs: next.durationMs ?? event.durationMs,
          error: next.error ?? event.error,
        }
      : event,
  )
}

export function statusTextForStreamEvent(event: StreamPayload): string | null {
  if (event.type === "memory_load_start") return "Reading memory"
  if (event.type === "memory_load_complete") return "Memory context ready"
  if (event.type === "agent_turn_start") return "Thinking"
  if (event.type === "agent_turn_complete") return "Planning next step"
  if (event.type === "tool_call_start" || event.type === "tool_executing") {
    const toolName = String(event.data?.tool_name ?? "tool")
    if (toolName === "WebSearch") return "Searching the web..."
    if (toolName === "WebFetch") return "Reading page..."
    return `Using ${toolName}...`
  }
  if (event.type === "tool_timeout") return "Tool timed out"
  if (event.type === "tool_error") return "Tool failed"
  if (event.type === "tool_complete") return "Tool finished"
  if (event.type === "agent_loop_limit") return "Agent loop reached its turn limit"
  if (event.type === "memory_update") return "Memory updated"
  if (event.type === "turn_complete") return null
  return null
}

export function compactNumber(value: number): string {
  return new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value)
}

export function friendlyErrorMessage(error: unknown): string {
  const raw = error instanceof Error ? error.message : String(error || "")
  if (/api[_ -]?key|unauthori[sz]ed|401|403|auth/i.test(raw)) {
    return "I could not reach the selected model because the API key or provider access is not ready. Check Settings, then try again."
  }
  if (/402|credit|can only afford|requires more credits|insufficient_quota|requested up to|max_tokens|token budget|context length|too many tokens/i.test(raw)) {
    return `The selected model could not start because this request exceeds the provider credit or token budget. Compact the chat, switch models, or add provider credits. (${raw})`
  }
  if (/429|rate[_-]?limit|ratelimit|quota.exceed/i.test(raw)) {
    return "The model provider is rate-limiting this request. Wait a moment, then try again."
  }
  if (/network|fetch|connection|timeout|timed out/i.test(raw)) {
    return "Geneva lost the connection while answering. Your chat is still here; try again when the server is reachable."
  }
  return "Geneva hit an unexpected problem while answering. Try again, or check Settings if this keeps happening."
}

export function projectDataErrorMessage(error: unknown): string {
  const raw = error instanceof Error ? error.message : String(error || "")
  if (/network|fetch|connection|timeout|timed out/i.test(raw)) {
    return "Projects could not sync because the server connection dropped. Your last project list is still shown."
  }
  if (/401|403|auth|unauthori[sz]ed/i.test(raw)) {
    return "Projects could not sync because local access is not ready. Check Settings, then retry."
  }
  return "Projects could not sync. Your last project list is still shown; retry when the server is reachable."
}
