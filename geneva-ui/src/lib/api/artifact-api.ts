import type { ArtifactDetail, ArtifactRecord } from "@/types"

import { jsonFetch } from "./core"

export type FetchArtifactsOptions = {
  sessionId?: string | null
  type?: string | null
  limit?: number
  signal?: AbortSignal
}

export async function fetchArtifacts({
  sessionId,
  type,
  limit = 50,
  signal,
}: FetchArtifactsOptions = {}): Promise<ArtifactRecord[]> {
  const params = new URLSearchParams()
  params.set("limit", String(limit))
  if (sessionId) params.set("session_id", sessionId)
  if (type) params.set("type", type)
  return jsonFetch<ArtifactRecord[]>(`/api/artifacts?${params.toString()}`, { signal })
}

export async function fetchArtifact(artifactId: string, signal?: AbortSignal): Promise<ArtifactDetail> {
  return jsonFetch<ArtifactDetail>(`/api/artifacts/${encodeURIComponent(artifactId)}`, { signal })
}

export async function deleteArtifact(artifactId: string): Promise<void> {
  await jsonFetch<{ ok: boolean; artifact_id: string }>(`/api/artifacts/${encodeURIComponent(artifactId)}`, {
    method: "DELETE",
  })
}
