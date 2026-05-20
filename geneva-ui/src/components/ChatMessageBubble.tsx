import { type ReactNode, useState } from "react"
import { motion } from "framer-motion"
import { Check, Copy, GitFork, Pencil, RotateCcw, ShieldCheck, Sparkles, ThumbsDown, ThumbsUp } from "lucide-react"

import { ActivityPanel, activityEventsForMessage, hasLiveThinkingEvent } from "@/components/ChatActivityPanel"
import { GenevaMark } from "@/components/GenevaMark"
import { MarkdownRenderer, ResearchCard, type CodePreview } from "@/components/ChatMarkdown"
import { ResearchPlanCard } from "@/components/ResearchPlanCard"
import { cn } from "@/lib/utils"
import type { ChatMessage, ContextDisclosureSummary } from "@/types"

export function MessageBubble({
  message,
  onForkMessage,
  onRetryMessage,
  onOpenArtifactPanel,
  onOpenArtifacts,
  onShowCodePreview,
  onSaveEdit,
  onStartResearch,
  onCancelResearchPlan,
  order,
}: {
  ghostMode: boolean
  message: ChatMessage
  onEditMessage?: (messageId: string) => void
  onForkMessage?: (messageId: string) => void
  onRememberMessage: (message: ChatMessage) => void
  onRetryMessage?: (messageId: string) => void
  onOpenArtifactPanel: (language: string, code: string) => void
  onOpenArtifacts?: () => void
  onShowCodePreview: (preview: CodePreview) => void
  onSaveEdit?: (serverId: string | undefined, frontendId: string, newText: string) => void
  onStartResearch?: (query: string) => void
  onCancelResearchPlan?: () => void
  order: number
}) {
  const isUser = message.role === "user"
  const isResearchBrief =
    !isUser &&
    message.content.length > 400 &&
    (message.content.match(/^## /gm)?.length ?? 0) >= 2
  const [copied, setCopied] = useState(false)
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null)
  const [editing, setEditing] = useState(false)
  const [editValue, setEditValue] = useState("")
  const activityEvents = isUser ? [] : activityEventsForMessage(message)
  const hasAssistantContent = message.content.trim().length > 0
  const showResponseGuide = Boolean(message.loading) && (hasAssistantContent || !hasLiveThinkingEvent(activityEvents, Boolean(message.loading)))

  function handleCopy() {
    void navigator.clipboard.writeText(message.content).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    })
  }

  if (message.researchPlan) {
    return (
      <motion.div animate={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 10 }} transition={{ duration: 0.2 }}>
        <ResearchPlanCard
          title={message.researchPlan.title}
          steps={message.researchPlan.steps}
          onStart={() => {
            onCancelResearchPlan?.()
            onStartResearch?.(message.researchPlan!.query)
          }}
          onCancel={() => onCancelResearchPlan?.()}
        />
      </motion.div>
    )
  }

  return (
    <motion.div
      animate={{ opacity: 1, y: 0 }}
      className={cn("message-row", isUser && "user")}
      initial={{ opacity: 0, y: 10 }}
      transition={{ delay: Math.min(order * 0.015, 0.12), duration: 0.18, ease: "easeOut" }}
    >
      <div className={cn("message-bubble", isUser ? "user-bubble" : "assistant-bubble")}>
        {isUser ? (
          <>
            {editing ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <textarea
                  autoFocus
                  onChange={(e) => setEditValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Escape") setEditing(false)
                    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                      const trimmed = editValue.trim()
                      if (trimmed) {
                        onSaveEdit?.(message.serverId, message.id, trimmed)
                      }
                      setEditing(false)
                    }
                  }}
                  rows={3}
                  style={{
                    width: "100%",
                    background: "var(--background)",
                    border: "1px solid var(--border, rgba(255,255,255,0.15))",
                    borderRadius: "8px",
                    color: "var(--foreground)",
                    fontSize: "14px",
                    padding: "8px 10px",
                    resize: "vertical",
                  }}
                  value={editValue}
                />
                <div style={{ display: "flex", gap: "6px", justifyContent: "flex-end" }}>
                  <button
                    onClick={() => setEditing(false)}
                    style={{ fontSize: "12px", opacity: 0.6, padding: "4px 10px" }}
                    type="button"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      const trimmed = editValue.trim()
                      if (trimmed) {
                        onSaveEdit?.(message.serverId, message.id, trimmed)
                      }
                      setEditing(false)
                    }}
                    style={{
                      background: "var(--primary, #6366f1)",
                      borderRadius: "6px",
                      color: "#fff",
                      fontSize: "12px",
                      padding: "4px 10px",
                    }}
                    type="button"
                  >
                    Save & Regenerate
                  </button>
                </div>
              </div>
            ) : (
              <div className="user-message-text">{message.content}</div>
            )}
            {!editing ? (
              <MessageActionRow
                copied={copied}
                isUser
                message={message}
                onCopy={handleCopy}
                onEditMessage={() => {
                  setEditValue(message.content)
                  setEditing(true)
                }}
              />
            ) : null}
          </>
        ) : (
          <>
            <SkillRunHeader message={message} />
            {activityEvents.length ? (
              <ActivityPanel
                error={message.error ?? null}
                events={activityEvents}
                hideLiveThinking={hasAssistantContent}
                loading={Boolean(message.loading)}
              />
            ) : null}
            {message.researchQuery || isResearchBrief ? (
              <ResearchCard
                message={message}
                onOpenArtifactPanel={onOpenArtifactPanel}
                onOpenArtifacts={onOpenArtifacts}
                onShowCodePreview={onShowCodePreview}
              />
            ) : (
              <div className="markdown-body">
                <MarkdownRenderer onOpenArtifactPanel={onOpenArtifactPanel} onShowCodePreview={onShowCodePreview}>
                  {message.content}
                </MarkdownRenderer>
              </div>
            )}
            {showResponseGuide ? (
              <div aria-label="Geneva is responding" className="assistant-writing-mark" role="status">
                <GenevaMark state="responding" variant="blob" />
              </div>
            ) : null}
            {!message.loading && message.contextSummary ? (
              <ContextDisclosureStrip summary={message.contextSummary} />
            ) : null}
            {!message.loading ? (
              <div className="assistant-actions">
                {message.timestamp ? (
                  <span className="message-timestamp" title={new Date(message.timestamp).toLocaleString()}>
                    {formatMessageTime(message.timestamp)}
                  </span>
                ) : (
                  <span />
                )}
                <MessageActionRow
                  copied={copied}
                  feedback={feedback}
                  message={message}
                  onCopy={handleCopy}
                  onFeedback={setFeedback}
                  onForkMessage={onForkMessage}
                  onRetryMessage={onRetryMessage}
                />
              </div>
            ) : null}
          </>
        )}
      </div>
    </motion.div>
  )
}

function SkillRunHeader({ message }: { message: ChatMessage }) {
  if (!message.skillName) return null
  return (
    <div className="skill-run-header" aria-label={`Using skill ${message.skillName}`}>
      <span className="skill-run-icon">
        <Sparkles className="size-3.5" />
      </span>
      <span className="skill-run-copy">
        <span>Using /{message.skillName}</span>
        {message.skillDescription ? <small>{message.skillDescription}</small> : null}
      </span>
      <span className="skill-run-chip">{skillScopeLabel(message.skillInvocationScope)}</span>
      <span className={`skill-run-chip safety-${message.skillSafetyStatus ?? "passed"}`}>
        <ShieldCheck className="size-3" />
        {skillSafetyLabel(message.skillSafetyStatus)}
      </span>
    </div>
  )
}

function skillScopeLabel(scope: ChatMessage["skillInvocationScope"]): string {
  if (scope === "chat") return "Session"
  if (scope === "project") return "Project"
  if (scope === "global") return "Global"
  return "Use once"
}

function skillSafetyLabel(status: string | null | undefined): string {
  if (status === "blocked") return "Blocked"
  if (status === "warning") return "Review"
  return "Safe"
}

function ContextDisclosureStrip({ summary }: { summary: ContextDisclosureSummary }) {
  const [open, setOpen] = useState(false)
  const modeLabel = summary.mode_label || summary.mode?.label
  const modeValue = modeLabel ? `${modeLabel} mode` : summary.model ? formatModelLabel(summary.model) : null
  const projectValue = summary.projects?.length ? summary.projects.join(", ") : null
  const memoryValue = summary.counts.memories ? `${summary.counts.memories} ${summary.counts.memories === 1 ? "memory" : "memories"} used` : null
  const sourceValue = summary.counts.sources ? `${summary.counts.sources} ${pluralize("source", summary.counts.sources)} used` : null
  const skillValue = summary.skills?.length ? summary.skills.map((name) => `/${name}`).join(", ") : null
  const toolValue = summary.tools?.length ? summary.tools.map(formatToolLabel).join(", ") : null
  const hasDetail = Boolean(
    summary.no_memory_write ||
      summary.trimmed ||
      projectValue ||
      memoryValue ||
      sourceValue ||
      skillValue ||
      toolValue ||
      modeValue,
  )

  return (
    <div className={cn("context-disclosure-strip", summary.no_memory_write && "is-ghost")}>
      <button
        aria-expanded={open}
        className="context-disclosure-trigger"
        disabled={!hasDetail}
        onClick={() => setOpen((value) => !value)}
        type="button"
      >
        <span className="context-disclosure-dot" />
        <span>{summary.summary}</span>
      </button>
      {open && hasDetail ? (
        <div aria-label="Context used for this answer" className="context-disclosure-panel" role="region">
          <TrustDetail label="Project" value={projectValue} />
          <TrustDetail label="Memory" value={memoryValue} />
          <TrustDetail label="Sources" value={sourceValue} />
          <TrustDetail label="Skill" value={skillValue} />
          <TrustDetail label="Tools" value={toolValue} />
          <TrustDetail label="Mode" value={modeValue} />
          <TrustDetail label="Budget" tone="muted" value={summary.trimmed ? "Some context was trimmed" : null} />
          <TrustDetail label="Privacy" tone="muted" value={summary.no_memory_write ? "No memory was written" : null} />
        </div>
      ) : null}
    </div>
  )
}

function TrustDetail({
  label,
  tone,
  value,
}: {
  label: string
  tone?: "default" | "muted"
  value: string | null | undefined
}) {
  if (!value) return null
  return (
    <div className={cn("context-detail-item", tone === "muted" && "muted")}>
      <span className="context-detail-label">{label}</span>
      <span className="context-detail-value">{value}</span>
    </div>
  )
}

function pluralize(word: string, count: number): string {
  return count === 1 ? word : `${word}s`
}

function formatModelLabel(model: string): string {
  const raw = model.trim()
  if (!raw) return "Selected model"
  const name = raw.includes("/") ? raw.split("/").at(-1) || raw : raw
  return name.replace(/[-_]+/g, " ")
}

function formatToolLabel(toolName: string): string {
  const raw = toolName.trim()
  const known: Record<string, string> = {
    AgentLoop: "Agent loop",
    BashCommand: "Run command",
    ListMcpResourcesTool: "List MCP resources",
    ReadFileTool: "Read file",
    ReadMcpResourceTool: "Read MCP resource",
    ToolSearch: "Find tool",
    WebFetch: "Read page",
    WebSearch: "Search web",
    WriteFileTool: "Edit file",
  }
  if (known[raw]) return known[raw]
  return raw
    .replace(/Tool$/, "")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .trim()
}

function MessageActionRow({
  copied,
  feedback,
  isUser = false,
  message,
  onCopy,
  onEditMessage,
  onFeedback,
  onForkMessage,
  onRetryMessage,
}: {
  copied: boolean
  feedback?: "up" | "down" | null
  isUser?: boolean
  message: ChatMessage
  onCopy: () => void
  onEditMessage?: () => void
  onFeedback?: (value: "up" | "down" | null | ((current: "up" | "down" | null) => "up" | "down" | null)) => void
  onForkMessage?: (messageId: string) => void
  onRetryMessage?: (messageId: string) => void
}) {
  return (
    <div className={cn("message-action-row", isUser && "user-actions")}>

      <IconButton label={copied ? "Copied!" : "Copy"} onClick={onCopy}>
        {copied ? <Check className="size-3.5 text-emerald-500" /> : <Copy className="size-3.5" />}
      </IconButton>
      {isUser ? (
        <IconButton label="Edit in composer" onClick={() => onEditMessage?.()}>
          <Pencil className="size-3.5" />
        </IconButton>
      ) : (
        <>
          <IconButton label="Retry response" onClick={() => onRetryMessage?.(message.id)}>
            <RotateCcw className="size-3.5" />
          </IconButton>
          {onForkMessage ? (
            <IconButton label="Fork from here" onClick={() => onForkMessage(message.id)}>
              <GitFork className="size-3.5" />
            </IconButton>
          ) : null}
        </>
      )}
      {!isUser && onFeedback ? (
        <>
          <IconButton
            label={feedback === "up" ? "Marked helpful" : "Mark helpful"}
            onClick={() => onFeedback((current) => (current === "up" ? null : "up"))}
            pressed={feedback === "up"}
          >
            <ThumbsUp className={cn("size-3.5", feedback === "up" && "text-emerald-500")} />
          </IconButton>
          <IconButton
            label={feedback === "down" ? "Marked unhelpful" : "Mark unhelpful"}
            onClick={() => onFeedback((current) => (current === "down" ? null : "down"))}
            pressed={feedback === "down"}
          >
            <ThumbsDown className={cn("size-3.5", feedback === "down" && "text-rose-500")} />
          </IconButton>
        </>
      ) : null}
    </div>
  )
}

function IconButton({
  children,
  label,
  onClick,
  pressed,
}: {
  children: ReactNode
  label: string
  onClick?: () => void
  pressed?: boolean
}) {
  return (
    <button
      aria-label={label}
      aria-pressed={pressed}
      className={cn("message-action-button", pressed && "active")}
      title={label}
      onClick={onClick}
      type="button"
    >
      {children}
    </button>
  )
}

function formatMessageTime(iso: string | undefined): string | null {
  if (!iso) return null
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return null
  const minutes = Math.floor((Date.now() - date.getTime()) / 60000)
  if (minutes < 1) return "just now"
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const timeStr = date.toLocaleTimeString("en", { hour: "2-digit", minute: "2-digit", hour12: false })
  const today = new Date()
  const isThisYear = date.getFullYear() === today.getFullYear()
  const dateStr = date.toLocaleDateString("en", { day: "numeric", month: "short", ...(isThisYear ? {} : { year: "numeric" }) })
  return `${dateStr} · ${timeStr}`
}
