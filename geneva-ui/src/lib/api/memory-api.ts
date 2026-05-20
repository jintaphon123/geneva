import type { AgentTraceRecord, ContextLedgerPayload, MemoryBrowserStats, MemoryConflict, MemoryConflictListResult, MemoryItem, MemoryListResult, MemoryStats, MemoryTimeline, MemoryWriteEvent, MemoryWriteEventListResult } from '@/types'

import { jsonFetch } from './core'
import type { RawMemoryStats } from './types'

export const emptyMemoryStats: MemoryStats = {
  active: 0,
  superseded: 0,
  archived: 0,
  expired: 0,
  lastIndexed: null,
  recent: [],
}

export async function fetchMemoryStats(sessionId?: string | null): Promise<MemoryStats> {
  const suffix = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ""
  const data = await jsonFetch<RawMemoryStats>(`/api/memory/stats${suffix}`)
  return normalizeMemoryStats(data)
}

export async function fetchContextLedger(
  sessionId?: string | null,
  limit = 20,
): Promise<ContextLedgerPayload> {
  const search = new URLSearchParams()
  if (sessionId) search.set("session_id", sessionId)
  search.set("limit", String(limit))
  const suffix = search.toString() ? `?${search.toString()}` : ""
  return jsonFetch<ContextLedgerPayload>(`/api/context/ledger${suffix}`)
}

export async function fetchAgentTraces(sessionId: string, limit = 50): Promise<AgentTraceRecord[]> {
  const search = new URLSearchParams({ limit: String(limit) })
  const data = await jsonFetch<{ records?: AgentTraceRecord[] }>(
    `/api/sessions/${encodeURIComponent(sessionId)}/agent-traces?${search.toString()}`,
  )
  return data.records ?? []
}

export async function fetchMemoryBrowserStats(): Promise<MemoryBrowserStats> {
  return jsonFetch<MemoryBrowserStats>("/api/memory/stats")
}

export async function rebuildMemoryIndex(): Promise<{ files_scanned: number }> {
  return jsonFetch<{ files_scanned: number }>("/api/memory/rebuild", {
    method: "POST",
  })
}

export async function listMemories(params?: {
  type?: string
  status?: string
  q?: string
  scope?: string
  limit?: number
  offset?: number
}): Promise<MemoryListResult> {
  const search = new URLSearchParams()
  if (params?.type && params.type !== "all") search.set("type", params.type)
  if (params?.status) search.set("status", params.status)
  if (params?.q) search.set("q", params.q)
  if (params?.scope) search.set("scope", params.scope)
  if (params?.limit) search.set("limit", String(params.limit))
  if (params?.offset) search.set("offset", String(params.offset))
  const suffix = search.toString() ? `?${search.toString()}` : ""
  return jsonFetch<MemoryListResult>(`/api/memory/list${suffix}`)
}

export async function searchMemories(q: string, type?: string): Promise<MemoryListResult> {
  const search = new URLSearchParams({ q })
  if (type && type !== "all") search.set("type", type)
  return jsonFetch<MemoryListResult>(`/api/memory/search?${search.toString()}`)
}

export async function fetchMemory(id: string): Promise<MemoryItem> {
  const data = await jsonFetch<{ memory: MemoryItem }>(`/api/memory/${encodeURIComponent(id)}`)
  return data.memory
}

export async function getMemoryTimeline(): Promise<MemoryTimeline> {
  const data = await jsonFetch<{ timeline?: MemoryTimeline }>("/api/memory/timeline")
  return data.timeline ?? []
}

export async function listMemoryConflicts(params?: {
  status?: string
  limit?: number
  offset?: number
}): Promise<MemoryConflictListResult> {
  const search = new URLSearchParams()
  if (params?.status) search.set("status", params.status)
  if (params?.limit) search.set("limit", String(params.limit))
  if (params?.offset) search.set("offset", String(params.offset))
  const suffix = search.toString() ? `?${search.toString()}` : ""
  return jsonFetch<MemoryConflictListResult>(`/api/memory/conflicts${suffix}`)
}

export async function listMemoryWriteEvents(params?: {
  sessionId?: string | null
  memoryId?: string | null
  status?: string
  limit?: number
  offset?: number
}): Promise<MemoryWriteEventListResult> {
  const search = new URLSearchParams()
  if (params?.sessionId) search.set("session_id", params.sessionId)
  if (params?.memoryId) search.set("memory_id", params.memoryId)
  if (params?.status) search.set("status", params.status)
  if (params?.limit) search.set("limit", String(params.limit))
  if (params?.offset) search.set("offset", String(params.offset))
  const suffix = search.toString() ? `?${search.toString()}` : ""
  return jsonFetch<MemoryWriteEventListResult>(`/api/memory/write-events${suffix}`)
}

export async function undoMemoryWriteEvent(id: string): Promise<{ event: MemoryWriteEvent }> {
  return jsonFetch<{ event: MemoryWriteEvent }>(`/api/memory/write-events/${encodeURIComponent(id)}/undo`, {
    method: "POST",
  })
}

export async function approveMemoryWriteEvent(id: string): Promise<{ event: MemoryWriteEvent }> {
  return jsonFetch<{ event: MemoryWriteEvent }>(`/api/memory/write-events/${encodeURIComponent(id)}/approve`, {
    method: "POST",
  })
}

export async function fetchMemoryConflict(id: string): Promise<MemoryConflict> {
  return jsonFetch<MemoryConflict>(`/api/memory/conflicts/${encodeURIComponent(id)}`)
}

export async function resolveMemoryConflict(
  id: string,
  resolution: "keep_existing" | "replace" | "merge",
  mergedContent?: string,
): Promise<{ operation?: string; memory_id?: string; conflict_id?: string; success: boolean; message?: string }> {
  return jsonFetch<{
    operation?: string
    memory_id?: string
    conflict_id?: string
    success: boolean
    message?: string
  }>(`/api/memory/conflicts/${encodeURIComponent(id)}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resolution, merged_content: mergedContent }),
  })
}

export async function addMemory(
  content: string,
  type: string,
  scope?: string,
): Promise<{ result: { operation: string; memory_id?: string | null; conflict_id?: string | null } }> {
  return jsonFetch<{ result: { operation: string; memory_id?: string | null; conflict_id?: string | null } }>(
    "/api/memory",
    {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, type, scope }),
    },
  )
}

export async function updateMemory(
  id: string,
  content: string,
): Promise<{ operation?: string; memory_id?: string; conflict_id?: string | null; success: boolean; message?: string }> {
  return jsonFetch<{
    operation?: string
    memory_id?: string
    conflict_id?: string | null
    success: boolean
    message?: string
  }>(
    `/api/memory/${encodeURIComponent(id)}`,
    {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
    },
  )
}

export async function archiveMemory(id: string): Promise<{ ok: boolean }> {
  return jsonFetch<{ ok: boolean }>(`/api/memory/${encodeURIComponent(id)}/archive`, {
    method: "POST",
  })
}

export async function deleteMemory(id: string): Promise<{ ok: boolean }> {
  return jsonFetch<{ ok: boolean }>(`/api/memory/${encodeURIComponent(id)}`, {
    method: "DELETE",
  })
}

function normalizeMemoryStats(raw: RawMemoryStats): MemoryStats {
  return {
    active: raw.stats?.total_active ?? raw.active ?? 0,
    superseded: raw.stats?.total_superseded ?? raw.superseded ?? 0,
    archived: raw.stats?.total_archived ?? raw.archived ?? 0,
    expired: raw.stats?.total_expired ?? raw.expired ?? 0,
    lastIndexed: raw.stats?.last_indexed ?? raw.last_indexed ?? null,
    recent: raw.recent ?? raw.memories ?? [],
  }
}
