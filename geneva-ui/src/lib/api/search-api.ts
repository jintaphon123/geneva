import type { SearchPayload, SearchResultType } from "@/types"

import { jsonFetch } from "./core"

type SearchGenevaOptions = {
  query: string
  projectId?: string | null
  types?: SearchResultType[]
  limit?: number
  signal?: AbortSignal
}

export async function searchGeneva({
  query,
  projectId,
  types,
  limit = 24,
  signal,
}: SearchGenevaOptions): Promise<SearchPayload> {
  const params = new URLSearchParams()
  params.set("q", query)
  params.set("limit", String(limit))
  if (projectId) params.set("project_id", projectId)
  if (types?.length) params.set("types", types.join(","))

  return jsonFetch<SearchPayload>(`/api/search?${params.toString()}`, { signal })
}
