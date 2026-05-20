import type { ModeListResult } from "@/types"

import { jsonFetch } from "./core"

export async function fetchModes(): Promise<ModeListResult> {
  return jsonFetch<ModeListResult>("/api/modes")
}
