import type { SettingsConfig, SystemStatus } from '@/types'

import { jsonFetch } from './core'

export async function fetchSettings(): Promise<{
  config: SettingsConfig
  cli: { gemini_ok: boolean; codex_ok: boolean }
}> {
  return jsonFetch<{
    config: SettingsConfig
    cli: { gemini_ok: boolean; codex_ok: boolean }
  }>("/api/settings")
}

export async function saveSettingsField(field: string, value: string | boolean): Promise<void> {
  await jsonFetch<{ ok: boolean }>("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ [field]: value }),
  })
}

export async function fetchSystemStatus(): Promise<SystemStatus> {
  return jsonFetch<SystemStatus>("/api/system/status")
}
