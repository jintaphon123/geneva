import { Children, type ComponentPropsWithoutRef, type ReactElement, type ReactNode, isValidElement, useState } from "react"
import { CheckCircle2, Clock3, PanelRight, Play, Telescope, Terminal, X } from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import { runCode } from "@/lib/api"
import { cn } from "@/lib/utils"
import type { ChatMessage, CodeRunResult } from "@/types"

export type CodePreview = {
  language: string
  code: string
  result: CodeRunResult
}

export function ResearchCard({
  message,
  onOpenArtifactPanel,
  onOpenArtifacts,
  onShowCodePreview,
}: {
  message: ChatMessage
  onOpenArtifactPanel: (language: string, code: string) => void
  onOpenArtifacts?: () => void
  onShowCodePreview: (preview: CodePreview) => void
}) {
  const progressItems = message.researchProgress ?? []
  const sources = message.researchSources ?? []
  const savedAsArtifact = Boolean(message.researchArtifactId)
  return (
    <div className="research-card">
      <div className="research-card-header">
        <div className="research-card-title">
          <span className="research-badge">
            <Telescope className="size-3.5" />
            Deep Research
          </span>
          {message.researchQuery ? (
            <span className="research-query">{message.researchQuery}</span>
          ) : null}
        </div>
        <div className="research-card-status-row">
          {savedAsArtifact ? (
            <button className="saved-badge artifact" onClick={onOpenArtifacts} type="button">
              <CheckCircle2 className="size-3.5" />
              Saved as report artifact
            </button>
          ) : null}
          {message.remembered ? <span className="saved-badge">Saved to memory</span> : null}
        </div>
      </div>
      {progressItems.length || message.loading ? (
        <div className="research-progress-timeline" aria-label="Deep Research progress">
          {progressItems.length ? (
            progressItems.map((item, index) => (
              <div className={cn("research-progress-row", item.status)} key={`${item.step}-${item.label}-${index}`}>
                <span>
                  {item.status === "complete" ? <CheckCircle2 className="size-3.5" /> : <Clock3 className="size-3.5" />}
                </span>
                <div>
                  <strong>{item.label || `Step ${item.step}`}</strong>
                  {item.detail ? <p>{item.detail}</p> : null}
                </div>
              </div>
            ))
          ) : (
            <div className="research-progress-row running">
              <span><Clock3 className="size-3.5" /></span>
              <div>
                <strong>Preparing research workspace</strong>
                <p>Geneva is creating a plan, running searches, and saving the final report as an artifact.</p>
              </div>
            </div>
          )}
        </div>
      ) : null}
      <div className="markdown-body">
        <MarkdownRenderer onOpenArtifactPanel={onOpenArtifactPanel} onShowCodePreview={onShowCodePreview}>
          {message.content}
        </MarkdownRenderer>
      </div>
      {sources.length ? (
        <div className="research-source-strip">
          <span>{sources.length} sources</span>
          {sources.slice(0, 3).map((source, index) => (
            <a href={source.url || undefined} key={`${source.source_id}-${index}`} rel="noreferrer" target={source.url ? "_blank" : undefined}>
              {source.source_id || `S${index + 1}`}
            </a>
          ))}
        </div>
      ) : null}
    </div>
  )
}

export function MarkdownRenderer({
  children,
  onOpenArtifactPanel,
  onShowCodePreview,
}: {
  children: string
  onOpenArtifactPanel: (language: string, code: string) => void
  onShowCodePreview: (preview: CodePreview) => void
}) {
  return (
    <ReactMarkdown
      components={{
        code: InlineCode,
        pre: (props) => (
          <CodeBlock
            {...props}
            onOpenArtifactPanel={onOpenArtifactPanel}
            onShowCodePreview={onShowCodePreview}
          />
        ),
      }}
      remarkPlugins={[remarkGfm]}
    >
      {children}
    </ReactMarkdown>
  )
}

function InlineCode({ children, className, ...props }: ComponentPropsWithoutRef<"code">) {
  return (
    <code className={typeof className === "string" ? className : undefined} {...props}>
      {children as ReactNode}
    </code>
  )
}

function CodeBlock({
  children,
  onOpenArtifactPanel,
  onShowCodePreview,
}: {
  children?: ReactNode
  onOpenArtifactPanel: (language: string, code: string) => void
  onShowCodePreview: (preview: CodePreview) => void
}) {
  const [running, setRunning] = useState(false)
  const child = Children.toArray(children)[0]
  const element = isValidElement(child) ? (child as ReactElement<{ children?: ReactNode; className?: string }>) : null
  const rawCode = element ? String(element.props.children ?? "").replace(/\n$/, "") : String(children ?? "")
  const language = normalizeLanguage(detectLanguage(element?.props.className ?? "", rawCode))
  const canPreview = ["html", "svg", "css"].includes(language)
  const canOpenCanvas = ["html", "svg", "python", "typescript", "javascript", "tsx", "jsx"].includes(language)

  async function handleRun() {
    if (running || !canPreview || !rawCode.trim()) return
    setRunning(true)
    try {
      const result = await runCode(language, rawCode)
      onShowCodePreview({ language: result.language || language, code: rawCode, result })
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="code-block">
      <div className="code-block-header">
        <span className="code-language">{language || "code"}</span>
        <div className="code-block-actions">
          {canOpenCanvas ? (
            <button
              aria-label="Open in Canvas"
              className="code-canvas-button"
              onClick={() => onOpenArtifactPanel(language, rawCode)}
              title="Open in Canvas"
              type="button"
            >
              <PanelRight className="size-3.5" />
            </button>
          ) : null}
          {canPreview ? (
            <button className="code-run-button" disabled={running} onClick={handleRun} type="button">
              <Play className="size-3.5" />
              {running ? "Opening" : "Preview"}
            </button>
          ) : null}
        </div>
      </div>
      <pre className="code-scroll">
        <code className={element?.props.className}>{rawCode}</code>
      </pre>
    </div>
  )
}

export function CodePreviewModal({
  onClose,
  preview,
}: {
  onClose: () => void
  preview: CodePreview
}) {
  const isHtml = preview.result.kind === "html"
  return (
    <div className="code-preview-backdrop">
      <div className="code-preview-modal">
        <div className="code-preview-header">
          <div className="code-preview-title">
            {isHtml ? <Play className="size-4" /> : <Terminal className="size-4" />}
            <span>{isHtml ? "Preview" : "Run output"}</span>
            <code>{preview.language || "code"}</code>
          </div>
          <button aria-label="Close preview" onClick={onClose} type="button">
            <X className="size-4" />
          </button>
        </div>
        {isHtml ? (
          <iframe
            className="code-preview-frame"
            sandbox="allow-scripts allow-modals"
            srcDoc={preview.result.output}
            title="Code preview"
          />
        ) : (
          <pre className={cn("code-output", !preview.result.ok && "error")}>
            {preview.result.output || preview.result.error || "No output"}
          </pre>
        )}
      </div>
    </div>
  )
}

function detectLanguage(className: string, code: string): string {
  const match = /language-([\w-]+)/.exec(className)
  if (match) return match[1].toLowerCase()
  const trimmed = code.trimStart().toLowerCase()
  if (trimmed.startsWith("<!doctype html") || trimmed.startsWith("<html")) return "html"
  if (trimmed.startsWith("<svg")) return "svg"
  return "text"
}

function normalizeLanguage(language: string): string {
  if (language === "js") return "javascript"
  if (language === "ts") return "typescript"
  if (language === "py") return "python"
  return language
}
