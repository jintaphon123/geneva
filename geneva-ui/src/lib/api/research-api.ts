import type { ResearchRun, ResearchRunListResult } from "@/types"

import { jsonFetch } from "./core"

export async function fetchResearchPlan(
  query: string,
  sessionId: string | null,
  provider: string | null,
  model: string | null,
): Promise<{ title: string; steps: string[] }> {
  const resp = await fetch("/api/research/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, session_id: sessionId, provider, model }),
  })
  if (!resp.ok) throw new Error(`Plan failed: ${resp.status}`)
  return (await resp.json()) as { title: string; steps: string[] }
}

export type FetchResearchRunsOptions = {
  sessionId?: string | null
  projectId?: string | null
  limit?: number
  signal?: AbortSignal
}

export async function fetchResearchRuns({
  sessionId,
  projectId,
  limit = 50,
  signal,
}: FetchResearchRunsOptions = {}): Promise<ResearchRunListResult> {
  const params = new URLSearchParams()
  params.set("limit", String(limit))
  if (sessionId) params.set("session_id", sessionId)
  if (projectId) params.set("project_id", projectId)
  return jsonFetch<ResearchRunListResult>(`/api/research/runs?${params.toString()}`, { signal })
}

export async function fetchResearchRun(runId: string, signal?: AbortSignal): Promise<ResearchRun> {
  const data = await jsonFetch<{ run: ResearchRun }>(`/api/research/runs/${encodeURIComponent(runId)}`, { signal })
  return data.run
}

export async function updateResearchRunStatus(
  runId: string,
  status: "stop" | "resume" | "fail",
  error?: string,
): Promise<ResearchRun> {
  const data = await jsonFetch<{ run: ResearchRun }>(
    `/api/research/runs/${encodeURIComponent(runId)}/${status}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(error ? { error } : {}),
    },
  )
  return data.run
}
