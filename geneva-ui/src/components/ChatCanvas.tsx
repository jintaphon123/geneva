import { type ReactNode, useCallback, useEffect, useLayoutEffect, useRef, useState } from "react"
import { ArrowDown, Brain, CheckCircle2, Code, Ghost, Pencil, Telescope, X } from "lucide-react"

import { ArtifactPanel, type Artifact } from "@/components/ArtifactPanel"
import { EmptyState } from "@/components/ChatEmptyState"
import { MessageBubble } from "@/components/ChatMessageBubble"
import { CodePreviewModal, type CodePreview } from "@/components/ChatMarkdown"
import { ProjectContextBanner } from "@/components/ChatProgressRail"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import type { ChatMessage, MemoryStats, MemoryWriteEvent, Project } from "@/types"

type ChatCanvasProps = {
  messages: ChatMessage[]
  memoryStats: MemoryStats
  loading: boolean
  statusText: string | null
  sessionTitle?: string | null
  activeProject: Project | null
  composer: ReactNode
  ghostMode: boolean
  onClearProject: () => void
  onEditMessage?: (messageId: string) => void
  onSaveEdit?: (serverId: string | undefined, frontendId: string, newText: string) => void
  onForkMessage?: (messageId: string) => void
  onRememberMessage: (message: ChatMessage) => void
  onRetryMessage?: (messageId: string) => void
  onToggleGhost: () => void
  onRenameSession?: (title: string) => void
  onQuickAction?: (action: string) => void
  onOpenArtifacts?: () => void
  onStartResearch?: (query: string) => void
  onCancelResearchPlan?: (id: string) => void
  memoryWriteNotice?: MemoryWriteEvent | null
  onUndoMemoryWrite?: (eventId: string) => void
  onReviewMemoryWrite?: (event: MemoryWriteEvent) => void
  onDismissMemoryWrite?: () => void
}

export function ChatCanvas({
  messages,
  memoryStats,
  loading,
  sessionTitle,
  activeProject,
  composer,
  ghostMode,
  onClearProject,
  onEditMessage,
  onSaveEdit,
  onForkMessage,
  onRememberMessage,
  onRetryMessage,
  onToggleGhost,
  onRenameSession,
  onQuickAction,
  onOpenArtifacts,
  onStartResearch,
  onCancelResearchPlan,
  memoryWriteNotice,
  onUndoMemoryWrite,
  onReviewMemoryWrite,
  onDismissMemoryWrite,
}: ChatCanvasProps) {
  const hasMessages = messages.length > 0
  const [codePreview, setCodePreview] = useState<CodePreview | null>(null)
  const [artifactPanel, setArtifactPanel] = useState<Artifact | null>(null)
  const [editingTitle, setEditingTitle] = useState(false)
  const [titleDraft, setTitleDraft] = useState("")
  const bottomRef = useRef<HTMLDivElement>(null)
  const scrollRootRef = useRef<HTMLDivElement | null>(null)
  const pinnedToBottomRef = useRef(true)
  const lastMessageIdRef = useRef<string | null>(null)
  const [showJumpToLatest, setShowJumpToLatest] = useState(false)

  const scrollToLatest = useCallback((behavior: ScrollBehavior = "auto") => {
    const viewport = getScrollViewport(scrollRootRef.current)
    if (!viewport) return
    window.requestAnimationFrame(() => {
      viewport.scrollTo({ top: viewport.scrollHeight, behavior })
      pinnedToBottomRef.current = true
      setShowJumpToLatest(false)
    })
  }, [])

  useEffect(() => {
    const viewport = getScrollViewport(scrollRootRef.current)
    if (!viewport) return
    const viewportElement: HTMLDivElement = viewport

    function updatePinnedState() {
      const distanceFromBottom =
        viewportElement.scrollHeight - viewportElement.scrollTop - viewportElement.clientHeight
      const pinned = distanceFromBottom < 96
      pinnedToBottomRef.current = pinned
      setShowJumpToLatest(!pinned && messages.length > 0)
    }

    updatePinnedState()
    viewportElement.addEventListener("scroll", updatePinnedState, { passive: true })
    return () => viewportElement.removeEventListener("scroll", updatePinnedState)
  }, [messages.length])

  useLayoutEffect(() => {
    const lastMessage = messages.at(-1)
    if (!lastMessage) {
      pinnedToBottomRef.current = true
      setShowJumpToLatest(false)
      lastMessageIdRef.current = null
      return
    }

    const previousLastId = lastMessageIdRef.current
    const lastChanged = previousLastId !== lastMessage.id
    const previousMessage = messages.length > 1 ? messages[messages.length - 2] : null
    const newTurnStarted = lastChanged && (lastMessage.role === "user" || previousMessage?.role === "user")
    if (newTurnStarted || pinnedToBottomRef.current) {
      scrollToLatest(lastChanged && !loading ? "smooth" : "auto")
    }
    lastMessageIdRef.current = lastMessage.id
  }, [loading, messages, scrollToLatest])

  function handleTitleClick() {
    if (!onRenameSession) return
    setTitleDraft(sessionTitle || "")
    setEditingTitle(true)
  }

  function commitTitle() {
    setEditingTitle(false)
    const trimmed = titleDraft.trim()
    if (trimmed && trimmed !== sessionTitle) onRenameSession?.(trimmed)
  }

  const handleOpenArtifactPanel = useCallback((language: string, code: string) => {
    setArtifactPanel({
      language,
      code,
      title: extractArtifactTitle(code, language),
    })
  }, [])

  return (
    <div
      className={cn(
        "chat-canvas",
        !hasMessages && "is-empty",
        ghostMode && "ghost-mode",
      )}
    >
      <div className="chat-primary">
        {ghostMode ? (
          <header className="ghost-mode-header">
            <div>
              <Ghost className="size-4" />
              <span>Incognito chat</span>
            </div>
            <button aria-label="Exit ghost mode" onClick={onToggleGhost} type="button">
              <X className="size-4" />
            </button>
          </header>
        ) : (
          <>
            <header className={cn("chat-header", !hasMessages && !activeProject && "empty-chat-header")}>
              {hasMessages || activeProject ? (
                <div className="chat-title-group">
                  {editingTitle ? (
                    <input
                      autoFocus
                      className="chat-title-input"
                      onBlur={commitTitle}
                      onChange={(e) => setTitleDraft(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") commitTitle()
                        if (e.key === "Escape") setEditingTitle(false)
                      }}
                      value={titleDraft}
                    />
                  ) : (
                    <button
                      className="chat-title"
                      onClick={handleTitleClick}
                      title={onRenameSession ? "Click to rename" : undefined}
                      type="button"
                    >
                      <span>{sessionTitle || "New chat"}</span>
                      {onRenameSession ? <Pencil className="size-3.5 text-muted-foreground opacity-60" /> : null}
                    </button>
                  )}
                  {activeProject ? (
                    <div className="project-chip">
                      <span className="project-chip-dot" style={{ background: activeProject.color }} />
                      <span>{activeProject.name}</span>
                      <button aria-label="Clear project" onClick={onClearProject} type="button">
                        <X className="size-3" />
                      </button>
                    </div>
                  ) : null}
                </div>
              ) : (
                <div aria-hidden="true" className="chat-title-spacer" />
              )}
            </header>
            <div className="chat-utility-stack">
              <button
                aria-label="Toggle ghost mode"
                aria-pressed={ghostMode}
                className="chat-top-button ghost-toggle"
                onClick={onToggleGhost}
                title="Ghost mode"
                type="button"
              >
                <Ghost className="size-4" />
              </button>
            </div>
          </>
        )}

        <div className="chat-canvas-with-artifact">
          {hasMessages ? (
            <ScrollArea className="chat-scroll" ref={scrollRootRef}>
              <div className="message-stack">
                {activeProject ? <ProjectContextBanner project={activeProject} /> : null}
                {messages.map((message, index) => (
                  <MessageBubble
                    ghostMode={ghostMode}
                    key={message.id}
                    message={message}
                    onEditMessage={onEditMessage}
                    onSaveEdit={onSaveEdit}
                    onForkMessage={onForkMessage}
                    onRememberMessage={onRememberMessage}
                    onRetryMessage={onRetryMessage}
                    onOpenArtifactPanel={handleOpenArtifactPanel}
                    onShowCodePreview={setCodePreview}
                    onOpenArtifacts={onOpenArtifacts}
                    onStartResearch={onStartResearch}
                    onCancelResearchPlan={onCancelResearchPlan ? () => onCancelResearchPlan(message.id) : undefined}
                    order={index}
                  />
                ))}
                <div ref={bottomRef} />
              </div>
            </ScrollArea>
          ) : (
            <div className="empty-shell">
              {activeProject ? <ProjectContextBanner project={activeProject} /> : null}
              <div className="empty-shell-centered">
                <EmptyState ghostMode={ghostMode} memoryStats={memoryStats} />
                <div className="empty-composer">{composer}</div>
                <div className="empty-quick-actions">
                  <button className="quick-action-btn" type="button" onClick={() => onQuickAction?.("Write a script to ")}>
                    <Pencil className="size-4" />
                    <span>Write</span>
                  </button>
                  <button className="quick-action-btn" type="button" onClick={() => onQuickAction?.("Explain how ")}>
                    <Brain className="size-4" />
                    <span>Learn</span>
                  </button>
                  <button className="quick-action-btn" type="button" onClick={() => onQuickAction?.("Review the code in ")}>
                    <Code className="size-4" />
                    <span>Code</span>
                  </button>
                  <button className="quick-action-btn" type="button" onClick={() => onQuickAction?.("Research ")}>
                    <Telescope className="size-4" />
                    <span>Research</span>
                  </button>
                </div>
              </div>
            </div>
          )}
          <ArtifactPanel artifact={artifactPanel} onClose={() => setArtifactPanel(null)} />
        </div>

        {memoryWriteNotice ? (
          <MemoryWriteToast
            event={memoryWriteNotice}
            onDismiss={onDismissMemoryWrite}
            onReview={onReviewMemoryWrite}
            onUndo={onUndoMemoryWrite}
          />
        ) : null}
        {hasMessages ? composer : null}
        {showJumpToLatest ? (
          <button
            aria-label="Jump to latest message"
            className="jump-to-latest"
            onClick={() => scrollToLatest("smooth")}
            title="Jump to latest"
            type="button"
          >
            <ArrowDown className="size-3.5" />
          </button>
        ) : null}
        {codePreview ? (
          <CodePreviewModal onClose={() => setCodePreview(null)} preview={codePreview} />
        ) : null}
      </div>
    </div>
  )
}

function MemoryWriteToast({
  event,
  onDismiss,
  onReview,
  onUndo,
}: {
  event: MemoryWriteEvent
  onDismiss?: () => void
  onReview?: (event: MemoryWriteEvent) => void
  onUndo?: (eventId: string) => void
}) {
  const isUndone = event.status === "undone"
  const isDraft = event.status === "draft"
  return (
    <div className={cn("memory-write-toast", isUndone && "is-undone", isDraft && "is-draft")}>
      <div className="memory-write-toast-icon">
        <CheckCircle2 className="size-3.5" />
      </div>
      <div className="memory-write-toast-copy">
        <div>{isUndone ? "Memory undone" : isDraft ? "Memory needs review" : "Saved to memory"}</div>
        <p>{event.user_visible_text}</p>
      </div>
      <div className="memory-write-toast-actions">
        {!isUndone ? (
          <button onClick={() => onUndo?.(event.id)} type="button">
            Undo
          </button>
        ) : null}
        <button onClick={() => onReview?.(event)} type="button">
          Review
        </button>
        <button aria-label="Dismiss memory notice" onClick={onDismiss} type="button">
          <X className="size-3.5" />
        </button>
      </div>
    </div>
  )
}

function getScrollViewport(root: HTMLDivElement | null): HTMLDivElement | null {
  return root?.querySelector<HTMLDivElement>("[data-scroll-viewport]") ?? null
}

function extractArtifactTitle(code: string, language: string): string {
  const firstLine = code.split("\n")[0].trim()
  const comment = firstLine
    .replace(/^(#|\/\/|\/\*|\*|<!--|--)\s*/, "")
    .replace(/(-->|\*\/)$/, "")
    .trim()
  if (comment && comment.length <= 60) return comment
  return `${language.charAt(0).toUpperCase() + language.slice(1)} snippet`
}
