export type ParsedSseFrame = {
  eventType: string | null
  data: unknown
}

export type RawMemoryStats = {
  stats?: {
    total_active?: number
    total_superseded?: number
    total_archived?: number
    total_expired?: number
    last_indexed?: string | null
  }
  active?: number
  superseded?: number
  archived?: number
  expired?: number
  last_indexed?: string | null
  recent?: import('@/types').MemoryItem[]
  memories?: import('@/types').MemoryItem[]
}

export type RawConversationMessage = {
  role?: string
  content?: unknown
  timestamp?: string
  id?: string
}
