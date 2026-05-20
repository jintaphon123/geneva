import type { ResearchSource, StreamPayload } from '@/types'

import { parseSseFrame, TRUSTED_REQUEST_HEADER } from './core'

type ResearchStepPayload = {
  step: number
  total: number
  label: string
  detail: string
  runId?: string | null
}

type ResearchCompletePayload = {
  text: string
  saved: boolean
  sessionId?: string | null
  runId?: string | null
  artifactId?: string | null
  sources?: ResearchSource[]
  qualityScore?: Record<string, unknown>
}

export type ImagePayload = {
  type: "base64"
  media_type: "image/jpeg" | "image/png" | "image/gif" | "image/webp"
  data: string
}

export async function streamChat(payload: {
  message: string
  sessionId: string | null
  providerName?: string | null
  model?: string | null
  modeId?: string | null
  projectId?: string | null
  ghostMode?: boolean
  images?: ImagePayload[]
  signal?: AbortSignal
  onText: (chunk: string) => void
  onEvent?: (event: StreamPayload) => void
  onSession?: (sessionId: string) => void
}): Promise<void> {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      [TRUSTED_REQUEST_HEADER]: "1",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      message: payload.message,
      user_input: payload.message,
      session_id: payload.sessionId,
      provider_name: payload.providerName,
      model: payload.model,
      mode_id: payload.modeId,
      max_turns: 100,
      project_id: payload.projectId,
      ghost_mode: Boolean(payload.ghostMode),
      images: payload.images ?? [],
    }),
    signal: payload.signal,
  })

  if (!response.ok || !response.body) {
    throw new Error(`Chat stream failed (${response.status})`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const frames = buffer.split("\n\n")
    buffer = frames.pop() ?? ""

    for (const frame of frames) {
      handleSseFrame(frame, payload)
    }
  }

  if (buffer.trim()) {
    handleSseFrame(buffer, payload)
  }
}

export async function streamResearch(payload: {
  query: string
  sessionId: string | null
  providerName?: string | null
  model?: string | null
  projectId?: string | null
  ghostMode?: boolean
  signal?: AbortSignal
  onStep: (step: ResearchStepPayload) => void
  onText: (chunk: string) => void
  onComplete: (result: ResearchCompletePayload) => void
  onError: (error: string) => void
}): Promise<void> {
  const response = await fetch("/api/research/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      [TRUSTED_REQUEST_HEADER]: "1",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      query: payload.query,
      session_id: payload.sessionId,
      provider_name: payload.providerName,
      model: payload.model,
      project_id: payload.projectId,
      ghost_mode: Boolean(payload.ghostMode),
    }),
    signal: payload.signal,
  })

  if (!response.ok || !response.body) {
    throw new Error(`Research stream failed (${response.status})`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const frames = buffer.split("\n\n")
    buffer = frames.pop() ?? ""

    for (const frame of frames) {
      handleResearchSseFrame(frame, payload)
    }
  }

  if (buffer.trim()) {
    handleResearchSseFrame(buffer, payload)
  }
}

function handleSseFrame(
  frame: string,
  callbacks: Pick<Parameters<typeof streamChat>[0], "onText" | "onEvent" | "onSession">,
): void {
  const parsed = parseSseFrame(frame)
  if (!parsed) return

  if (!parsed.data || typeof parsed.data !== "object") {
    return
  }
  const event = parsed.data as StreamPayload
  if (!event.type && parsed.eventType) event.type = parsed.eventType

  const sessionId = event.data?.session_id
  if (typeof sessionId === "string" && sessionId.trim()) {
    callbacks.onSession?.(sessionId)
  }

  callbacks.onEvent?.(event)

  if (event.type === "text_delta") {
    const text = event.data?.text
    if (typeof text === "string") callbacks.onText(text)
  }

  if (event.type === "error") {
    const message = event.error?.message || "The assistant ran into an error."
    callbacks.onText(`\n\n${message}`)
  }
}

function handleResearchSseFrame(
  frame: string,
  callbacks: Pick<
    Parameters<typeof streamResearch>[0],
    "onStep" | "onText" | "onComplete" | "onError"
  >,
): void {
  const parsed = parseSseFrame(frame)
  if (!parsed) return

  const rawData = parsed.data
  const eventRecord =
    rawData && typeof rawData === "object" ? (rawData as Record<string, unknown>) : {}
  const eventType = parsed.eventType ?? String(eventRecord.type ?? "")
  const dataRecord =
    eventRecord.data && typeof eventRecord.data === "object"
      ? (eventRecord.data as Record<string, unknown>)
      : eventRecord

  if (eventType === "research_step") {
    callbacks.onStep({
      step: Number(dataRecord.step ?? 0),
      total: Number(dataRecord.total ?? 0),
      label: String(dataRecord.label ?? ""),
      detail: String(dataRecord.detail ?? ""),
      runId: typeof dataRecord.run_id === "string" ? dataRecord.run_id : null,
    })
  }

  if (eventType === "research_text") {
    const chunk = dataRecord.chunk
    if (typeof chunk === "string") callbacks.onText(chunk)
  }

  if (eventType === "research_complete") {
    callbacks.onComplete({
      text: typeof dataRecord.text === "string" ? dataRecord.text : "",
      saved: Boolean(dataRecord.saved),
      sessionId: typeof dataRecord.session_id === "string" ? dataRecord.session_id : null,
      runId: typeof dataRecord.run_id === "string" ? dataRecord.run_id : null,
      artifactId: typeof dataRecord.artifact_id === "string" ? dataRecord.artifact_id : null,
      sources: Array.isArray(dataRecord.sources)
        ? dataRecord.sources.filter((item): item is ResearchSource => isResearchSource(item))
        : [],
      qualityScore:
        dataRecord.quality_score && typeof dataRecord.quality_score === "object" && !Array.isArray(dataRecord.quality_score)
          ? (dataRecord.quality_score as Record<string, unknown>)
          : {},
    })
  }

  if (eventType === "research_error") {
    callbacks.onError(String(dataRecord.error ?? "Research failed."))
  }
}

function isResearchSource(value: unknown): value is ResearchSource {
  if (!value || typeof value !== "object") return false
  const record = value as Record<string, unknown>
  return typeof record.title === "string" || typeof record.source_id === "string"
}
