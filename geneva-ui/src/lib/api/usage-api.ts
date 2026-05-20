import type { UsageSummary } from "@/types"

import { jsonFetch } from "./core"

export async function fetchUsage(): Promise<UsageSummary> {
  return jsonFetch<UsageSummary>("/api/usage")
}
