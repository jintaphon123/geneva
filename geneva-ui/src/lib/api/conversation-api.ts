import type { AgentTraceRecord, ChatMessage, ContextDisclosureSummary, ContextLedgerEntry, ContextLedgerPayload, ContextLedgerRecord, SessionSummary, ToolTraceEvent } from '@/types'

import { jsonFetch } from './core'
import { fetchAgentTraces, fetchContextLedger } from './memory-api'
import type { RawConversationMessage } from './types'

const INTERNAL_CONTEXT_SOURCE_TYPES = new Set([
  "assembled_extra_system_prompt",
  "conversation_history",
  "ghost_privacy_contract",
  "pending_user_input",
  "runtime_base_context",
])
const MEMORY_CONTEXT_SOURCE_TYPES = new Set(["fallback_memory_context", "memory_context"])

export async function fetchSessions(): Promise<SessionSummary[]> {
  const data = await jsonFetch<{ sessions?: SessionSummary[] }>("/api/sessions")
  return data.sessions ?? []
}

export async function fetchSessionTraces(sessionId: string): Promise<AgentTraceRecord[]> {
  try {
    const result = await jsonFetch<{ records: AgentTraceRecord[] }>(
      `/api/sessions/${encodeURIComponent(sessionId)}/agent-traces`,
    )
    return result.records ?? []
  } catch {
    return []
  }
}

export function attachTracesToMessages(
  messages: ChatMessage[],
  traces: AgentTraceRecord[],
): ChatMessage[] {
  if (!traces.length) return messages

  const tracesByIndex = new Map<number, AgentTraceRecord>()
  traces.forEach((trace, idx) => {
    tracesByIndex.set(idx, trace)
  })

  let assistantIdx = 0

  return messages.map((message) => {
    if (message.role !== "assistant" || message.loading) return message

    const trace = tracesByIndex.get(assistantIdx)
    assistantIdx++

    if (!trace) return message

    const traceEvents = trace.events ?? []
    const toolEvents: ToolTraceEvent[] = traceEvents
      .filter((e) => e.tool_name && e.status && e.kind !== "agent_turn_start" && e.kind !== "agent_turn_complete")
      .map((e, i) => ({
        id: e.tool_call_id ?? `${trace.created_at}-${i}`,
        toolCallId: e.tool_call_id,
        toolName: e.tool_name,
        status: e.is_error ? "error" : (e.status as ToolTraceEvent["status"]),
        summary: e.summary ?? undefined,
        inputPreview: e.input_preview ?? undefined,
        outputPreview: e.output_preview ?? undefined,
        error: e.error ?? undefined,
        durationMs: e.duration_ms ?? undefined,
        timeoutSeconds: e.timeout_seconds ?? undefined,
        turnIndex: e.turn_index,
      }))

    const memoryEvents: ToolTraceEvent[] = []
    if (trace.memory_action !== undefined && trace.memory_action !== null) {
      const activeChars = trace.memory_active_chars
      const memorySummary = activeChars
        ? `Memory ready · ${Math.round(activeChars / 1000)}k chars active`
        : "Memory ready · ? chars active"
      memoryEvents.push({
        id: `${trace.created_at}-mem-ready`,
        toolName: "Memory",
        status: "complete",
        summary: memorySummary,
        inputPreview: undefined,
        outputPreview: undefined,
        error: undefined,
        durationMs: undefined,
        timeoutSeconds: undefined,
      })

      const actionLabel =
        trace.memory_action === "ADD" ? "ADD"
          : trace.memory_action === "UPDATE" ? "UPDATE"
          : trace.memory_action === "NOOP" ? "NOOP"
          : "no changes"
      memoryEvents.push({
        id: `${trace.created_at}-mem-update`,
        toolName: "Memory",
        status: "complete",
        summary: `Memory updated · ${actionLabel}`,
        inputPreview: undefined,
        outputPreview: undefined,
        error: undefined,
        durationMs: undefined,
        timeoutSeconds: undefined,
      })
    }

    const allEvents = [
      ...memoryEvents.slice(0, 1),
      ...toolEvents,
      ...memoryEvents.slice(1),
    ]

    return { ...message, toolEvents: allEvents.length ? allEvents : message.toolEvents }
  })
}

export async function fetchSessionMessages(sessionId: string): Promise<ChatMessage[]> {
  const [data, traces, contextLedger] = await Promise.all([
    jsonFetch<{ messages?: RawConversationMessage[] }>(`/api/sessions/${encodeURIComponent(sessionId)}/messages`),
    fetchAgentTraces(sessionId).catch(() => []),
    fetchContextLedger(sessionId, 50).catch(() => null),
  ])
  const messages: ChatMessage[] = []
  const toolIndex = new Map<string, { messageIndex: number; eventIndex: number }>()
  const traceById = buildTraceLookup(traces)

  for (const [index, rawMessage] of (data.messages ?? []).entries()) {
    if (rawMessage.role !== "user" && rawMessage.role !== "assistant") continue

    if (rawMessage.role === "assistant") {
      const text = extractTextContent(rawMessage.content)
      const toolEvents: ToolTraceEvent[] = extractToolUses(rawMessage.content).map((toolUse) => {
        const persisted = traceById.get(toolUse.id || "")
        return {
          id: `${sessionId}-${toolUse.id || index}-${toolUse.name}`,
          toolCallId: toolUse.id,
          toolName: persisted?.toolName ?? toolUse.name ?? "Tool",
          status: persisted?.status ?? "running",
          summary: persisted?.summary ?? summarizeRawToolInput(toolUse.name, toolUse.input),
          inputPreview: persisted?.inputPreview ?? previewUnknown(toolUse.input),
          outputPreview: persisted?.outputPreview,
          error: persisted?.error ?? null,
          durationMs: persisted?.durationMs ?? null,
          timeoutSeconds: persisted?.timeoutSeconds ?? null,
          turnIndex: persisted?.turnIndex ?? null,
        }
      })
      const message: ChatMessage = {
        id: `${sessionId}-${index}`,
        role: "assistant",
        content: text,
        remembered: false,
        toolEvents,
        timestamp: rawMessage.timestamp,
        serverId: rawMessage.id,
      }
      messages.push(message)
      const messageIndex = messages.length - 1
      toolEvents.forEach((event, eventIndex) => {
        if (event.toolCallId) toolIndex.set(event.toolCallId, { messageIndex, eventIndex })
      })
      continue
    }

    const toolResults = extractToolResults(rawMessage.content)
    if (toolResults.length) {
      for (const result of toolResults) {
        const target = result.toolUseId ? toolIndex.get(result.toolUseId) : undefined
        if (!target) continue
        const owner = messages[target.messageIndex]
        const events = [...(owner.toolEvents ?? [])]
        const current = events[target.eventIndex]
        events[target.eventIndex] = {
          ...current,
          status: result.isError ? "error" : "complete",
          outputPreview: previewUnknown(result.content),
          error: result.isError ? previewUnknown(result.content) : null,
        }
        messages[target.messageIndex] = { ...owner, toolEvents: events }
      }
      continue
    }

    const content = flattenContent(rawMessage.content)
    if (!content.trim()) continue
    messages.push({
      id: `${sessionId}-${index}`,
      role: "user",
      content,
      remembered: false,
      timestamp: rawMessage.timestamp,
      serverId: rawMessage.id,
    })
  }

  return attachContextSummariesToMessages(
    messages.filter((message) => message.content.trim() || (message.toolEvents?.length ?? 0) > 0),
    contextLedger,
  )
}

function attachContextSummariesToMessages(
  messages: ChatMessage[],
  payload: ContextLedgerPayload | null,
): ChatMessage[] {
  const summaries = contextSummariesFromLedger(payload)
  if (!summaries.length) return messages

  const assistantIndexes = messages
    .map((message, index) => ({ index, message }))
    .filter(({ message }) => message.role === "assistant" && !message.loading)
    .map(({ index }) => index)
  if (!assistantIndexes.length) return messages

  const relevantIndexes = assistantIndexes.slice(Math.max(0, assistantIndexes.length - summaries.length))
  return messages.map((message, index) => {
    const summaryIndex = relevantIndexes.indexOf(index)
    if (summaryIndex === -1 || message.contextSummary) return message
    return { ...message, contextSummary: summaries[summaryIndex] }
  })
}

function contextSummariesFromLedger(payload: ContextLedgerPayload | null): ContextDisclosureSummary[] {
  const records = payload?.history?.length ? payload.history : payload?.records?.length ? payload.records : payload?.latest ? [payload.latest] : []
  return [...records]
    .reverse()
    .map(contextSummaryFromLedgerRecord)
    .filter((summary): summary is ContextDisclosureSummary => summary !== null)
}

function contextSummaryFromLedgerRecord(record: ContextLedgerRecord): ContextDisclosureSummary | null {
  const included = record.entries.filter(isIncludedContextEntry)
  const projectEntries = included.filter((entry) => entry.source_type === "project_context")
  const memoryEntries = included.filter((entry) => MEMORY_CONTEXT_SOURCE_TYPES.has(entry.source_type))
  const skillEntries = included.filter((entry) => entry.source_type === "skill_context")
  const sourceEntries = included.filter((entry) => {
    if (INTERNAL_CONTEXT_SOURCE_TYPES.has(entry.source_type)) return false
    if (MEMORY_CONTEXT_SOURCE_TYPES.has(entry.source_type)) return false
    return entry.source_type !== "project_context" && entry.source_type !== "skill_context"
  })
  const metadata = record.metadata ?? {}
  const modeLabel = optionalText(metadata.mode_label)
  const skillNames = uniqueStrings(skillEntries.map(skillNameFromEntry))
  const memoryCount = memoryEntries.reduce((total, entry) => total + memoryCountFromEntry(entry), 0)
  const projectName = projectNameFromEntries(projectEntries)
  const ghostMode = Boolean(metadata.ghost_mode)
  const parts: string[] = []

  if (ghostMode) parts.push("Ghost mode: no memory write")
  if (modeLabel) parts.push(`${modeLabel} mode`)
  if (projectEntries.length) parts.push(`Used ${projectName} project`)
  if (memoryCount) parts.push(`${memoryCount} ${memoryCount === 1 ? "memory" : "memories"}`)
  if (sourceEntries.length) parts.push(`${sourceEntries.length} source${sourceEntries.length === 1 ? "" : "s"}`)
  if (skillNames.length) parts.push(skillNames.map((name) => `/${name}`).join(" / "))

  return {
    session_id: record.session_id,
    turn_id: optionalText(metadata.turn_id),
    ledger_id: record.id,
    summary: parts.length ? parts.join(" · ") : "No extra context used",
    counts: {
      projects: projectEntries.length,
      memories: memoryCount,
      sources: sourceEntries.length,
      skills: skillNames.length,
      tools: 0,
    },
    projects: projectEntries.map((entry) => entryLabel(entry)),
    skills: skillNames,
    tools: [],
    mode_id: optionalText(metadata.mode_id),
    mode_label: modeLabel,
    route_reason: optionalText(metadata.route_reason),
    cost_tier: optionalText(metadata.cost_tier),
    model: record.model,
    ghost_mode: ghostMode,
    no_memory_write: ghostMode,
    trimmed: record.entries.some((entry) => entry.action === "trimmed"),
    budget: record.budget ?? {},
    created_at: record.created_at,
  }
}

function isIncludedContextEntry(entry: ContextLedgerEntry): boolean {
  return ["included", "preserved", "trimmed"].includes(entry.action) && Number(entry.tokens_after) > 0
}

function entryLabel(entry: ContextLedgerEntry): string {
  const metadata = entry.metadata ?? {}
  return optionalText(metadata.project_name) ?? optionalText(entry.label) ?? entry.source_type
}

function projectNameFromEntries(entries: ContextLedgerEntry[]): string {
  if (!entries.length) return "current"
  return optionalText(entries[0].metadata?.project_name) ?? "current"
}

function skillNameFromEntry(entry: ContextLedgerEntry): string {
  const name = optionalText(entry.metadata?.skill_name) ?? optionalText(entry.label)?.replace(/^Active skill:\s*/i, "")
  return (name ?? "").trim().replace(/^\//, "")
}

function memoryCountFromEntry(entry: ContextLedgerEntry): number {
  const raw = entry.metadata?.memory_count
  if (typeof raw === "number" && raw > 0) return Math.round(raw)
  return 1
}

function uniqueStrings(values: string[]): string[] {
  return values.filter((value, index, source) => Boolean(value) && source.indexOf(value) === index)
}

function optionalText(value: unknown): string | null {
  const text = String(value ?? "").trim()
  return text || null
}

export async function fetchConversationTitle(sessionId: string): Promise<string> {
  const data = await jsonFetch<{ title?: string }>(
    `/api/conversations/${encodeURIComponent(sessionId)}/title`,
  )
  return data.title ?? ""
}

export async function saveConversationTitle(sessionId: string, title: string): Promise<void> {
  await jsonFetch<{ ok: boolean }>(`/api/conversations/${encodeURIComponent(sessionId)}/title`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  })
}

export async function amendConversation(sessionId: string, message: string): Promise<void> {
  await jsonFetch<{ ok: boolean }>(`/api/sessions/${encodeURIComponent(sessionId)}/amend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, text: message }),
  })
}

export async function pinSession(sessionId: string): Promise<{ pinned: boolean }> {
  return jsonFetch<{ ok: boolean; pinned: boolean }>(`/api/sessions/${encodeURIComponent(sessionId)}/pin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  }).then((r) => ({ pinned: r.pinned ?? false }))
}

export async function addSessionToProject(
  projectId: string,
  sessionId: string,
): Promise<{ ok: boolean }> {
  return jsonFetch<{ ok: boolean }>(`/api/projects/${encodeURIComponent(projectId)}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  })
}

export async function generateConversationTitle(
  sessionId: string,
  firstMessage: string,
  providerName?: string | null,
  model?: string | null,
): Promise<string> {
  const data = await jsonFetch<{ title?: string }>(
    `/api/conversations/${encodeURIComponent(sessionId)}/title/generate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        first_message: firstMessage,
        provider_name: providerName ?? null,
        model: model ?? null,
      }),
    },
  )
  return data.title ?? ""
}

export async function executeCommand(payload: {
  raw: string
  sessionId: string | null
  providerName?: string | null
  model?: string | null
}): Promise<{ text: string; sessionId: string | null; type?: string }> {
  const data = await jsonFetch<{
    type?: string
    output?: string
    result?: string
    error?: string
    message?: string
    session_id?: string
  }>("/api/command", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      raw: payload.raw,
      session_id: payload.sessionId,
      provider_name: payload.providerName,
      model: payload.model,
    }),
  })
  return {
    text: data.output ?? data.result ?? data.message ?? data.error ?? "",
    sessionId: data.session_id ?? payload.sessionId,
    type: data.type,
  }
}

function flattenContent(content: unknown): string {
  if (typeof content === "string") return content
  if (!Array.isArray(content)) return ""

  return content
    .map((item) => {
      if (typeof item === "string") return item
      if (!item || typeof item !== "object") return ""
      const record = item as Record<string, unknown>
      if (typeof record.text === "string") return record.text
      if (typeof record.content === "string") return record.content
      if (typeof record.name === "string") return `[${record.name}]`
      return ""
    })
    .filter(Boolean)
    .join("\n")
}

function extractTextContent(content: unknown): string {
  if (typeof content === "string") return content
  if (!Array.isArray(content)) return ""
  return content
    .map((item) => {
      if (!item || typeof item !== "object") return ""
      const record = item as Record<string, unknown>
      return record.type === "text" && typeof record.text === "string" ? record.text : ""
    })
    .filter(Boolean)
    .join("\n")
}

function extractToolUses(content: unknown): Array<{ id: string | null; name: string; input: unknown }> {
  if (!Array.isArray(content)) return []
  return content.flatMap((item) => {
    if (!item || typeof item !== "object") return []
    const record = item as Record<string, unknown>
    if (record.type !== "tool_use") return []
    return [{
      id: typeof record.id === "string" ? record.id : null,
      name: typeof record.name === "string" ? record.name : "Tool",
      input: record.input,
    }]
  })
}

function extractToolResults(
  content: unknown,
): Array<{ toolUseId: string | null; content: unknown; isError: boolean }> {
  if (!Array.isArray(content)) return []
  return content.flatMap((item) => {
    if (!item || typeof item !== "object") return []
    const record = item as Record<string, unknown>
    if (record.type !== "tool_result") return []
    return [{
      toolUseId: typeof record.tool_use_id === "string" ? record.tool_use_id : null,
      content: record.content,
      isError: Boolean(record.is_error),
    }]
  })
}

function previewUnknown(value: unknown, limit = 700): string {
  if (value == null) return ""
  const text = typeof value === "string" ? value : JSON.stringify(value, null, 2)
  if (text.length <= limit) return text
  return `${text.slice(0, limit - 18).trimEnd()}\n[truncated]`
}

function buildTraceLookup(records: AgentTraceRecord[]): Map<string, Partial<ToolTraceEvent>> {
  const traceById = new Map<string, Partial<ToolTraceEvent>>()

  for (const record of records) {
    for (const event of record.events ?? []) {
      const toolCallId = event.tool_call_id
      if (!toolCallId) continue

      const current = traceById.get(toolCallId) ?? {}
      traceById.set(toolCallId, {
        ...current,
        toolCallId,
        toolName: event.tool_name ?? current.toolName ?? "Tool",
        status: normalizeTraceStatus(event.status, event.kind, event.error),
        summary: event.summary ?? current.summary,
        inputPreview: event.input_preview ?? current.inputPreview,
        outputPreview: event.output_preview ?? current.outputPreview,
        error: event.error ?? current.error ?? null,
        durationMs:
          typeof event.duration_ms === "number" ? event.duration_ms : current.durationMs,
        timeoutSeconds:
          typeof event.timeout_seconds === "number" ? event.timeout_seconds : current.timeoutSeconds,
        turnIndex: typeof event.turn_index === "number" ? event.turn_index : current.turnIndex,
      })
    }
  }

  return traceById
}

function normalizeTraceStatus(
  status?: string | null,
  kind?: string,
  error?: string | null,
): ToolTraceEvent["status"] {
  if (kind === "tool_timeout") return "timeout"
  if (kind === "tool_error") return "error"
  if (kind === "tool_result") return error ? "error" : "complete"
  return status || "running"
}

function summarizeRawToolInput(toolName: string, input: unknown): string {
  if (!input || typeof input !== "object") return ""
  const record = input as Record<string, unknown>
  const lowered = toolName.toLowerCase()
  const filePath = record.file_path ?? record.filePath ?? record.path
  if (["read", "write", "edit"].includes(lowered) && typeof filePath === "string") {
    return filePath
  }
  const query = record.query ?? record.pattern ?? record.url ?? record.command
  return typeof query === "string" ? query : ""
}
