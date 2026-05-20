import type { KeyboardEvent } from "react"
import { AlertTriangle, RotateCcw, Trash2, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { Project, SessionSummary } from "@/types"

export const PROJECT_COLORS = ["#6366f1", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#3b82f6"]

export const PROJECT_MEMORY_TYPES = [
  { label: "Decision", value: "project" },
  { label: "Source", value: "reference" },
  { label: "Reflection", value: "feedback" },
  { label: "Personal context", value: "user" },
]

export type ProjectNotice = {
  title: string
  detail: string
  retry?: () => void
}

export type TodoAction = "toggle" | "delete" | "edit"

type ProjectInfoModalProps = {
  localName: string
  localDescription: string
  localContext: string
  localColor: string
  saving: boolean
  onClose: () => void
  onSave: (fields?: Partial<Pick<Project, "name" | "description" | "context_md" | "color" | "pinned">>) => void
  onSetColor: (value: string) => void
  onSetContext: (value: string) => void
  onSetDescription: (value: string) => void
  onSetName: (value: string) => void
}

type ProjectDeleteModalProps = {
  deleteError: string | null
  deletingProject: boolean
  localName: string
  onClose: () => void
  onConfirm: () => void
}

export function ProjectNoticeBanner({
  notice,
  onDismiss,
}: {
  notice: ProjectNotice
  onDismiss: () => void
}) {
  return (
    <div className="project-error-notice" role="status">
      <AlertTriangle className="size-4" />
      <div>
        <strong>{notice.title}</strong>
        <p>{notice.detail}</p>
      </div>
      <div className="project-error-actions">
        {notice.retry ? (
          <button onClick={notice.retry} type="button">
            <RotateCcw className="size-3.5" />
            Retry
          </button>
        ) : null}
        <button aria-label="Dismiss project notice" onClick={onDismiss} type="button">
          <X className="size-3.5" />
        </button>
      </div>
    </div>
  )
}

export function ProjectInfoModal({
  localName,
  localDescription,
  localContext,
  localColor,
  saving,
  onClose,
  onSave,
  onSetColor,
  onSetContext,
  onSetDescription,
  onSetName,
}: ProjectInfoModalProps) {
  function saveOnEnter(event: KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) {
    if (event.key === "Enter" && event.metaKey) {
      event.preventDefault()
      onSave()
    }
  }

  return (
    <div className="project-modal-backdrop" role="presentation">
      <div aria-modal="true" className="project-modal project-info-modal" role="dialog">
        <div className="project-modal-header">
          <div>
            <h2>Project Info</h2>
            <p>Saved context is injected into every project conversation.</p>
          </div>
          <button aria-label="Close project info" onClick={onClose} type="button">
            <X className="size-4" />
          </button>
        </div>

        <label className="project-label" htmlFor="project-name">
          Name
        </label>
        <input
          className="project-input"
          id="project-name"
          onBlur={() => onSave()}
          onChange={(event) => onSetName(event.target.value)}
          onKeyDown={saveOnEnter}
          value={localName}
        />

        <label className="project-label" htmlFor="project-description">
          Description
        </label>
        <textarea
          className="project-textarea compact"
          id="project-description"
          onBlur={() => onSave()}
          onChange={(event) => onSetDescription(event.target.value)}
          onKeyDown={saveOnEnter}
          rows={3}
          value={localDescription}
        />

        <div className="project-label">Color</div>
        <div className="project-color-row">
          {PROJECT_COLORS.map((color) => (
            <button
              aria-label={`Use ${color}`}
              className={cn("project-color-dot", color === localColor && "active")}
              key={color}
              onClick={() => {
                onSetColor(color)
                onSave({ color })
              }}
              style={{ background: color }}
              type="button"
            />
          ))}
        </div>

        <label className="project-label" htmlFor="project-context">
          Context
        </label>
        <textarea
          className="project-textarea"
          id="project-context"
          onBlur={() => onSave()}
          onChange={(event) => onSetContext(event.target.value)}
          onKeyDown={saveOnEnter}
          placeholder="Describe this project -- injected into every conversation as context..."
          rows={8}
          value={localContext}
        />
        <div className="project-info-actions">
          <Button disabled={saving} onClick={() => onSave()}>
            {saving ? "Saving..." : "Save"}
          </Button>
          <Button onClick={onClose} variant="quiet">
            Done
          </Button>
        </div>
      </div>
    </div>
  )
}

export function ProjectDeleteModal({
  deleteError,
  deletingProject,
  localName,
  onClose,
  onConfirm,
}: ProjectDeleteModalProps) {
  return (
    <div className="project-modal-backdrop" role="presentation">
      <div aria-modal="true" className="project-modal project-delete-modal" role="dialog">
        <div className="project-modal-header">
          <div className="project-delete-title">
            <span className="project-delete-icon">
              <Trash2 className="size-4" />
            </span>
            <div>
              <h2>Delete project?</h2>
              <p>This removes the project surface and all attached project tasks.</p>
            </div>
          </div>
          <button
            aria-label="Close delete project confirmation"
            disabled={deletingProject}
            onClick={onClose}
            type="button"
          >
            <X className="size-4" />
          </button>
        </div>
        <div className="project-delete-summary">
          <span>{localName || "Untitled project"}</span>
          <p>Project memories remain in the memory system, but the project workspace and links will be deleted.</p>
        </div>
        {deleteError ? (
          <div className="project-delete-error">
            <AlertTriangle className="size-4" />
            <span>{deleteError}</span>
          </div>
        ) : null}
        <div className="project-modal-actions">
          <Button disabled={deletingProject} onClick={onClose} variant="quiet">
            Cancel
          </Button>
          <Button
            className="project-danger-button"
            disabled={deletingProject}
            onClick={onConfirm}
            type="button"
          >
            {deletingProject ? "Deleting..." : "Delete project"}
          </Button>
        </div>
      </div>
    </div>
  )
}

export function sessionTitle(session: SessionSummary): string {
  if (session.title) return session.title
  if (session.updated_at) return `Chat from ${session.updated_at.slice(0, 10)}`
  const dateFromId = dateFromSessionId(session.session_id)
  if (dateFromId) return `Chat from ${dateFromId}`
  return session.session_id.slice(0, 12)
}

export function todoActionKey(action: TodoAction, todoId: string): string {
  return `${action}:${todoId}`
}

export function userFacingError(error: unknown): string {
  if (error instanceof Error && error.message.trim()) return error.message.trim()
  if (typeof error === "string" && error.trim()) return error.trim()
  return "Geneva could not complete this action. Retry after checking the local server."
}

export function formatDate(value?: string): string {
  if (!value) return "No date"
  const dateFromId = dateFromSessionId(value)
  if (dateFromId) return dateFromId
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value.slice(0, 10)
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })
}

function dateFromSessionId(value: string): string | null {
  const match = /^(\d{4})(\d{2})(\d{2})/.exec(value)
  return match ? `${match[1]}-${match[2]}-${match[3]}` : null
}
