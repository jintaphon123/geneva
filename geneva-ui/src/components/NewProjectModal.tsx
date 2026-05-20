import { useState } from "react"
import { AlertTriangle, RotateCcw, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { createProject } from "@/lib/api"
import { cn } from "@/lib/utils"
import type { Project } from "@/types"

const PROJECT_COLORS = ["#6366f1", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#3b82f6"]

type NewProjectModalProps = {
  onClose: () => void
  onCreated: (project: Project) => void
}

export function NewProjectModal({ onClose, onCreated }: NewProjectModalProps) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [color, setColor] = useState(PROJECT_COLORS[0])
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleCreate() {
    const trimmedName = name.trim()
    if (!trimmedName || creating) return
    setCreating(true)
    setError(null)
    try {
      const project = await createProject(trimmedName, description.trim(), { color })
      onCreated(project)
    } catch (caught) {
      setError(projectCreationErrorMessage(caught))
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="project-modal-backdrop" role="presentation">
      <div aria-labelledby="new-project-title" aria-modal="true" className="project-modal" role="dialog">
        <div className="project-modal-header">
          <h2 id="new-project-title">New Project</h2>
          <Button aria-label="Close" disabled={creating} onClick={onClose} size="compactIcon" variant="quiet">
            <X className="size-4" />
          </Button>
        </div>
        <label className="project-label" htmlFor="new-project-name">
          Project name
        </label>
        <input
          autoFocus
          className="project-input"
          id="new-project-name"
          aria-describedby={error ? "new-project-error" : undefined}
          aria-invalid={Boolean(error)}
          onChange={(event) => {
            setName(event.target.value)
            if (error) setError(null)
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter") void handleCreate()
          }}
          value={name}
        />
        <label className="project-label" htmlFor="new-project-description">
          What is this project about?
        </label>
        <textarea
          className="project-textarea compact"
          id="new-project-description"
          onChange={(event) => {
            setDescription(event.target.value)
            if (error) setError(null)
          }}
          rows={4}
          value={description}
        />
        <div className="project-label">Color</div>
        <div className="project-color-row">
          {PROJECT_COLORS.map((option) => (
            <button
              aria-label={`Use ${option}`}
              className={cn("project-color-dot", option === color && "active")}
              key={option}
              onClick={() => {
                setColor(option)
                if (error) setError(null)
              }}
              style={{ background: option }}
              type="button"
            />
          ))}
        </div>
        {error ? (
          <div className="project-modal-error" id="new-project-error" role="alert">
            <AlertTriangle className="size-4" />
            <span>{error}</span>
            <button disabled={creating || !name.trim()} onClick={() => void handleCreate()} type="button">
              <RotateCcw className="size-3.5" />
              Retry
            </button>
          </div>
        ) : null}
        <div className="project-modal-actions">
          <Button disabled={creating} onClick={onClose} variant="subtle">
            Cancel
          </Button>
          <Button disabled={!name.trim() || creating} onClick={() => void handleCreate()}>
            {creating ? "Creating..." : "Create Project"}
          </Button>
        </div>
      </div>
    </div>
  )
}

function projectCreationErrorMessage(error: unknown): string {
  const raw = error instanceof Error ? error.message : String(error || "")
  if (/Project name is required/i.test(raw)) return "Add a project name before creating this project."
  if (/network|fetch|connection|timeout|timed out/i.test(raw)) {
    return "Geneva could not reach the project store. Your draft stayed here; retry when the server is back."
  }
  return "Geneva could not create this project. Your draft stayed here; retry or check the local server."
}
