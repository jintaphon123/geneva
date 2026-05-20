import type { CodeRunResult, SessionActivityPayload, SlashCommand, ToolSpecMeta } from '@/types'

import { jsonFetch } from './core'

export async function fetchCommands(): Promise<SlashCommand[]> {
  const data = await jsonFetch<{ commands?: SlashCommand[] }>("/api/commands")
  return data.commands ?? []
}

export async function fetchTools(): Promise<ToolSpecMeta[]> {
  const data = await jsonFetch<{ tools?: ToolSpecMeta[] }>("/api/tools")
  return data.tools ?? []
}

export async function resolveToolPermission(
  sessionId: string,
  requestId: string,
  approved: boolean,
): Promise<void> {
  await jsonFetch<{ ok: boolean }>(
    `/api/sessions/${encodeURIComponent(sessionId)}/tool-permissions/${encodeURIComponent(requestId)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved }),
    },
  )
}

export async function fetchSessionActivity(sessionId: string, limit = 50): Promise<SessionActivityPayload> {
  const search = new URLSearchParams({ limit: String(limit) })
  return jsonFetch<SessionActivityPayload>(
    `/api/sessions/${encodeURIComponent(sessionId)}/activity?${search.toString()}`,
  )
}

export async function runCode(language: string, code: string): Promise<CodeRunResult> {
  return jsonFetch<CodeRunResult>("/api/code/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ language, code }),
  })
}
