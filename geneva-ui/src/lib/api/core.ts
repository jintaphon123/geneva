import type { ParsedSseFrame } from './types'

export const TRUSTED_REQUEST_HEADER = 'X-Second-Brain-Request'

export async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, withTrustedRequestHeader(init))
  if (!response.ok) {
    const message = await readErrorMessage(response)
    throw new Error(message || `${url} failed (${response.status})`)
  }
  return (await response.json()) as T
}

function withTrustedRequestHeader(init?: RequestInit): RequestInit | undefined {
  const method = (init?.method ?? "GET").toUpperCase()
  if (method === "GET" || method === "HEAD") return init
  const headers = new Headers(init?.headers)
  headers.set(TRUSTED_REQUEST_HEADER, "1")
  return { ...init, headers }
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const text = await response.text()
    if (!text.trim()) return `Request failed (${response.status})`
    try {
      const data = JSON.parse(text) as { error?: unknown; message?: unknown }
      const message = data.error ?? data.message
      if (typeof message === "string" && message.trim()) return message.trim()
    } catch {
      return text.slice(0, 180)
    }
    return `Request failed (${response.status})`
  } catch {
    return `Request failed (${response.status})`
  }
}

export function parseSseFrame(frame: string): ParsedSseFrame | null {
  const dataLines: string[] = []
  let eventType: string | null = null

  for (const rawLine of frame.split(/\r?\n/)) {
    const line = rawLine.trimEnd()
    if (line.startsWith("event:")) {
      eventType = line.slice(6).trimStart()
    }
    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart())
    }
  }

  if (!dataLines.length) return null

  try {
    return {
      eventType,
      data: JSON.parse(dataLines.join("\n")),
    }
  } catch {
    return null
  }
}

