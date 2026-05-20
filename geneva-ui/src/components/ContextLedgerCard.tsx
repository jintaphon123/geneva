import { Activity, Gauge, Scissors } from "lucide-react"

import { cn } from "@/lib/utils"
import type { ContextLedgerEntry, ContextLedgerPayload, ContextLedgerRecord } from "@/types"

type ContextLedgerCardProps = {
  error: string | null
  payload: ContextLedgerPayload | null
  className?: string
  emptyText?: string
  maxEntries?: number
}

export function ContextLedgerCard({
  className,
  emptyText = "Context decisions will appear after the next chat turn.",
  error,
  maxEntries = 5,
  payload,
}: ContextLedgerCardProps) {
  const record = payload?.latest ?? payload?.records?.[0] ?? payload?.history?.[0] ?? null
  const entries = (record?.entries ?? []).slice(0, maxEntries)
  const tokensAfter = Number(record?.totals?.tokens_after ?? 0)
  const tokensSaved = Number(record?.totals?.tokens_saved ?? 0)
  const percentUsed = readPercentUsed(record)

  return (
    <section className={cn("context-ledger-card w-full max-w-full min-w-0 overflow-hidden", className)}>
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-[13px] font-medium text-foreground">
          <Gauge className="size-3.5 text-primary" />
          Context Inspector
        </div>
        {record ? (
          <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">
            {record.event === "compact" ? "Compact" : "Turn"}
          </span>
        ) : null}
      </div>

      {record ? (
        <div className="w-full max-w-full min-w-0 overflow-hidden rounded-[10px] border border-border/75 bg-card/78 p-3">
          <div className="grid grid-cols-2 gap-2">
            <MiniMetric label="Used" value={percentUsed === null ? "n/a" : `${percentUsed}%`} />
            <MiniMetric label="After" value={formatTokenCount(tokensAfter)} />
            <MiniMetric label="Saved" value={formatTokenCount(tokensSaved)} />
          </div>

          {percentUsed !== null ? (
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-muted">
              <div
                className={cn(
                  "h-full rounded-full transition-[width,background] duration-200",
                  percentUsed >= 90
                    ? "bg-destructive"
                    : percentUsed >= 75
                      ? "bg-amber-500"
                      : "bg-primary",
                )}
                style={{ width: `${Math.max(3, Math.min(percentUsed, 100))}%` }}
              />
            </div>
          ) : null}

          <div className="mt-3 space-y-2">
            {entries.map((entry, index) => (
              <LedgerEntryRow entry={entry} key={`${entry.source_type}-${entry.action}-${index}`} />
            ))}
          </div>

          <div className="mt-3 flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
            <span className="truncate">{record.model || "unknown model"}</span>
            <span>{record.created_at ? formatRelative(record.created_at) : ""}</span>
          </div>
        </div>
      ) : (
        <div className="rounded-[10px] border border-dashed border-border p-4 text-sm text-muted-foreground">
          {error ?? emptyText}
        </div>
      )}
    </section>
  )
}

export function readContextPercentUsed(payload: ContextLedgerPayload | null): number | null {
  const record = payload?.latest ?? payload?.records?.[0] ?? payload?.history?.[0] ?? null
  return readPercentUsed(record)
}

function LedgerEntryRow({ entry }: { entry: ContextLedgerEntry }) {
  const saved = Number(entry.tokens_saved ?? Math.max(0, entry.tokens_before - entry.tokens_after))
  const Icon = entry.action === "trimmed" || entry.action === "compacted" ? Scissors : Activity
  return (
    <div className="context-ledger-entry w-full max-w-full min-w-0 rounded-[8px] border border-border/60 bg-background/45 px-2.5 py-2">
      <div className="context-ledger-entry-header flex items-center justify-between gap-2">
        <div className="flex w-full max-w-full min-w-0 items-center gap-2">
          <Icon className={cn("size-3.5 shrink-0", actionTone(entry.action))} />
          <span className="truncate text-[12px] font-medium text-foreground">
            {entry.label || labelFromSource(entry.source_type)}
          </span>
        </div>
        <span className={cn("context-ledger-entry-action max-w-[86px] shrink-0 truncate rounded-full px-2 py-0.5 text-[10.5px] font-medium", actionPill(entry.action))}>
          {entry.action}
        </span>
      </div>
      <div className="mt-1 line-clamp-2 break-words text-[11.5px] leading-4 text-muted-foreground">{entry.reason}</div>
      <div className="context-ledger-token-row mt-2 flex min-w-0 flex-wrap items-center justify-between gap-x-2 gap-y-1 text-[11px] text-muted-foreground">
        <span className="min-w-0 truncate">{formatTokenCount(entry.tokens_after)} kept</span>
        {saved > 0 ? (
          <span className="min-w-0 truncate text-right">{formatTokenCount(saved)} saved</span>
        ) : (
          <span className="min-w-0 truncate text-right">{formatTokenCount(entry.tokens_before)} seen</span>
        )}
      </div>
    </div>
  )
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-[8px] bg-muted/58 px-2 py-1.5">
      <div className="text-[12.5px] font-semibold leading-none text-foreground">{value}</div>
      <div className="mt-1 text-[10.5px] text-muted-foreground">{label}</div>
    </div>
  )
}

function readPercentUsed(record: ContextLedgerRecord | null): number | null {
  const raw = record?.budget?.percent_used
  if (typeof raw === "number" && Number.isFinite(raw)) return Math.round(raw)
  return null
}

function formatTokenCount(value: number): string {
  if (!Number.isFinite(value) || value <= 0) return "0"
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}m`
  if (value >= 1000) return `${(value / 1000).toFixed(value >= 10_000 ? 0 : 1)}k`
  return String(Math.round(value))
}

function labelFromSource(sourceType: string): string {
  return sourceType
    .split("_")
    .filter(Boolean)
    .map((part) => part[0]?.toUpperCase() + part.slice(1))
    .join(" ")
}

function actionTone(action: string): string {
  if (action === "compacted") return "text-amber-600"
  if (action === "trimmed") return "text-blue-600"
  if (action === "preserved") return "text-emerald-600"
  if (action === "omitted") return "text-muted-foreground"
  return "text-primary"
}

function actionPill(action: string): string {
  if (action === "compacted") return "bg-amber-500/12 text-amber-700"
  if (action === "trimmed") return "bg-blue-500/12 text-blue-700"
  if (action === "preserved") return "bg-emerald-500/12 text-emerald-700"
  if (action === "omitted") return "bg-muted text-muted-foreground"
  return "bg-primary/10 text-primary"
}

function formatRelative(value: string): string {
  const timestamp = Date.parse(value)
  if (!Number.isFinite(timestamp)) return "unknown"
  const seconds = Math.max(0, Math.floor((Date.now() - timestamp) / 1000))
  if (seconds < 60) return "just now"
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} hr ago`
  const days = Math.floor(hours / 24)
  return `${days} day${days === 1 ? "" : "s"} ago`
}
