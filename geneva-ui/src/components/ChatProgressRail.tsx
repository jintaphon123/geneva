import { useState } from "react"
import { Check, ChevronDown, ChevronUp, Circle, ListChecks, LoaderCircle, PanelRightClose, Pin, Target } from "lucide-react"

import { cn } from "@/lib/utils"
import type { Project } from "@/types"

export function ProjectContextBanner({ project }: { project: Project }) {
  const [expanded, setExpanded] = useState(false)
  if (!project.context_md.trim()) return null

  return (
    <div className="project-context-banner">
      <button
        className="project-context-header"
        onClick={() => setExpanded((value) => !value)}
        type="button"
      >
        <span className="project-dot" style={{ background: project.color }} />
        <span>{project.name}</span>
        <span className="project-context-status">Context active</span>
        {expanded ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
      </button>
      {expanded ? (
        <div className="project-context-preview">{project.context_md.slice(0, 300)}</div>
      ) : null}
    </div>
  )
}

export function ProgressRail({
  loading,
  onClose,
  onToggleProjectTodo,
  project,
  statusText,
}: {
  loading: boolean
  onClose: () => void
  onToggleProjectTodo?: (todoId: string) => void
  project: Project | null
  statusText: string | null
}) {
  const total = project?.todos.length ?? 0
  const done = project?.todos.filter((todo) => todo.done).length ?? 0
  const percent = total ? Math.round((done / total) * 100) : loading ? 35 : 0
  const openCount = Math.max(0, total - done)
  const sortedTodos = project
    ? [...project.todos].sort((a, b) => {
        if (a.done !== b.done) return a.done ? 1 : -1
        return a.position - b.position
      })
    : []
  const nextTodo = sortedTodos.find((todo) => !todo.done)

  return (
    <aside className="progress-rail" aria-label="Progress">
      <div className="progress-rail-header">
        <div>
          <div className="progress-rail-title">
            <ListChecks className="size-4" />
            Progress
          </div>
          <p>{project ? project.name : loading ? "Current run" : "No active project"}</p>
        </div>
        <button aria-label="Hide progress" onClick={onClose} type="button">
          <PanelRightClose className="size-4" />
        </button>
      </div>

      <div className={cn("progress-status-card", loading && "running")}>
        <div className="progress-status-icon">
          {loading ? <LoaderCircle className="size-4 animate-spin" /> : <Pin className="size-4" />}
        </div>
        <div>
          <span>{loading ? "Agent running" : project ? "Project plan pinned" : "Progress hidden by default"}</span>
          <p>
            {loading
              ? statusText || "Geneva is working through the current step."
              : nextTodo?.text || "Open a project or start a task to pin steps here."}
          </p>
        </div>
      </div>

      <div className="progress-meter">
        <div className="progress-meter-label">
          <span>{project ? `${openCount} open · ${done} done` : loading ? "Running" : "Idle"}</span>
          <strong>{percent}%</strong>
        </div>
        <div className="progress-meter-track">
          <span style={{ width: `${Math.max(loading && !project ? 18 : 0, percent)}%` }} />
        </div>
      </div>

      {project ? (
        <div className="progress-step-list agent">
          {sortedTodos.map((todo) => (
            <label className={cn("progress-step", todo.done && "done")} key={todo.id}>
              <input
                checked={todo.done}
                onChange={() => onToggleProjectTodo?.(todo.id)}
                type="checkbox"
              />
              <span className="progress-step-icon">
                {todo.done ? <Check className="size-3.5" /> : <Circle className="size-3.5" />}
              </span>
              <span>{todo.text}</span>
            </label>
          ))}
          {sortedTodos.length === 0 ? (
            <div className="progress-empty">
              <Target className="size-4" />
              Add goals in the project workspace, then they will stay pinned here during project chats.
            </div>
          ) : null}
        </div>
      ) : (
        <div className="progress-empty">
          <Target className="size-4" />
          {loading
            ? statusText || "Geneva is working through the current step."
            : "Open a project to pin goals here. Normal chats stay clean until you ask for this rail."}
        </div>
      )}
    </aside>
  )
}
