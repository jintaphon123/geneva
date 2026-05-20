import { type KeyboardEvent, useCallback, useEffect, useMemo, useState } from "react"
import {
  Activity,
  ArrowLeft,
  BookOpenCheck,
  Brain,
  Check,
  Database,
  ExternalLink,
  FileText,
  Folder,
  Layers,
  ListChecks,
  LockKeyhole,
  MessageSquare,
  MoreVertical,
  Pencil,
  Pin,
  Plus,
  RotateCcw,
  Settings2,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react"

import {
  PROJECT_MEMORY_TYPES,
  ProjectDeleteModal,
  ProjectInfoModal,
  ProjectNoticeBanner,
  type ProjectNotice,
  type TodoAction,
  formatDate,
  sessionTitle,
  todoActionKey,
  userFacingError,
} from "@/components/ProjectViewSupport"
import { ProjectArtifactsPanel } from "@/components/ProjectArtifactsPanel"
import { Button } from "@/components/ui/button"
import {
  addMemory,
  addProjectTextSource,
  addTodo,
  archiveProject,
  deleteProject,
  deleteProjectSource,
  deleteTodo,
  fetchProjectSessions,
  fetchProjectSourcePreview,
  fetchProjectSources,
  listMemories,
  toggleTodo,
  updateProject,
  updateProjectSource,
  updateTodoText,
} from "@/lib/api"
import { cn } from "@/lib/utils"
import type { MemoryItem, Project, ProjectSource, ProjectSourcePreview, SessionSummary, Todo } from "@/types"

type ProjectViewProps = {
  project: Project
  onClose: () => void
  onUpdate: (updated: Project) => void
  onOpenChat: (projectId: string, sessionId?: string) => void
}

type ProjectWorkspaceTab =
  | "overview"
  | "conversations"
  | "memories"
  | "sources"
  | "tasks"
  | "artifacts"
  | "settings"

type ProjectSourceDraftType = "text" | "markdown" | "url"

const PROJECT_WORKSPACE_TABS: Array<{ id: ProjectWorkspaceTab; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "conversations", label: "Conversations" },
  { id: "memories", label: "Memories" },
  { id: "sources", label: "Sources" },
  { id: "tasks", label: "Tasks" },
  { id: "artifacts", label: "Artifacts" },
  { id: "settings", label: "Settings" },
]

const SOURCE_STATUS_LABELS: Record<string, string> = {
  pending: "Parsing",
  ready: "Ready",
  failed: "Failed",
  unsupported: "Unsupported",
  stale: "Stale",
}

function sourceStatusLabel(source: ProjectSource): string {
  if (source.include_policy === "exclude") return "Excluded"
  return SOURCE_STATUS_LABELS[source.parse_status] ?? source.parse_status
}

function sourceStatusClass(source: ProjectSource): string {
  if (source.include_policy === "exclude") return "excluded"
  return source.parse_status || "ready"
}

function sourceTypeLabel(source: ProjectSource): string {
  return source.source_type.toUpperCase()
}

export function ProjectView({ project, onClose, onUpdate, onOpenChat }: ProjectViewProps) {
  const [localName, setLocalName] = useState(project.name)
  const [localDescription, setLocalDescription] = useState(project.description)
  const [localContext, setLocalContext] = useState(project.context_md)
  const [localColor, setLocalColor] = useState(project.color)
  const [localTodos, setLocalTodos] = useState<Todo[]>(project.todos)
  const [newTodoText, setNewTodoText] = useState("")
  const [editingTodoId, setEditingTodoId] = useState<string | null>(null)
  const [editingTodoText, setEditingTodoText] = useState("")
  const [activeTab, setActiveTab] = useState<ProjectWorkspaceTab>("overview")
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [projectMemories, setProjectMemories] = useState<MemoryItem[]>([])
  const [projectSources, setProjectSources] = useState<ProjectSource[]>([])
  const [sourcePreview, setSourcePreview] = useState<ProjectSourcePreview | null>(null)
  const [memoryDraft, setMemoryDraft] = useState("")
  const [memoryType, setMemoryType] = useState("project")
  const [sourceDraftType, setSourceDraftType] = useState<ProjectSourceDraftType>("text")
  const [sourceDraftTitle, setSourceDraftTitle] = useState("")
  const [sourceDraftContent, setSourceDraftContent] = useState("")
  const [saving, setSaving] = useState(false)
  const [savingMemory, setSavingMemory] = useState(false)
  const [sourceSaving, setSourceSaving] = useState(false)
  const [addingTask, setAddingTask] = useState(false)
  const [loadingSessions, setLoadingSessions] = useState(false)
  const [loadingMemories, setLoadingMemories] = useState(false)
  const [loadingSources, setLoadingSources] = useState(false)
  const [pendingTodoAction, setPendingTodoAction] = useState<string | null>(null)
  const [pendingSourceAction, setPendingSourceAction] = useState<string | null>(null)
  const [projectNotice, setProjectNotice] = useState<ProjectNotice | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [actionsOpen, setActionsOpen] = useState(false)
  const [showAllSessions, setShowAllSessions] = useState(false)
  const [infoOpen, setInfoOpen] = useState(false)
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [deletingProject, setDeletingProject] = useState(false)
  const [mobileRailOpen, setMobileRailOpen] = useState(false)

  const reportProjectNotice = useCallback((title: string, error: unknown, retry?: () => void) => {
    setProjectNotice({
      title,
      detail: userFacingError(error),
      retry,
    })
  }, [])

  const loadProjectSessions = useCallback(
    async (projectId: string) => {
      setLoadingSessions(true)
      try {
        const result = await fetchProjectSessions(projectId)
        setSessions(result)
      } catch (error) {
        setSessions([])
        reportProjectNotice(
          "Project chats could not load",
          error,
          () => void loadProjectSessions(projectId),
        )
      } finally {
        setLoadingSessions(false)
      }
    },
    [reportProjectNotice],
  )

  const loadProjectMemories = useCallback(
    async (projectId: string) => {
      setLoadingMemories(true)
      try {
        const result = await listMemories({
          scope: projectId,
          status: "active",
          limit: 12,
          offset: 0,
        })
        setProjectMemories(result.items)
      } catch (error) {
        setProjectMemories([])
        reportProjectNotice(
          "Project memory could not load",
          error,
          () => void loadProjectMemories(projectId),
        )
      } finally {
        setLoadingMemories(false)
      }
    },
    [reportProjectNotice],
  )

  const loadProjectSources = useCallback(
    async (projectId: string) => {
      setLoadingSources(true)
      try {
        const [sources, preview] = await Promise.all([
          fetchProjectSources(projectId),
          fetchProjectSourcePreview(projectId),
        ])
        setProjectSources(sources)
        setSourcePreview(preview)
      } catch (error) {
        setProjectSources([])
        setSourcePreview(null)
        reportProjectNotice(
          "Project sources could not load",
          error,
          () => void loadProjectSources(projectId),
        )
      } finally {
        setLoadingSources(false)
      }
    },
    [reportProjectNotice],
  )

  useEffect(() => {
    setLocalName(project.name)
    setLocalDescription(project.description)
    setLocalContext(project.context_md)
    setLocalColor(project.color)
    setLocalTodos(project.todos)
    setActiveTab("overview")
    setProjectNotice(null)
    setDeleteError(null)
    setMobileRailOpen(false)
    void loadProjectSessions(project.id)
    void loadProjectMemories(project.id)
    void loadProjectSources(project.id)
  }, [project, loadProjectMemories, loadProjectSessions, loadProjectSources])

  useEffect(() => {
    if (!mobileRailOpen) return
    function closeOnEscape(event: globalThis.KeyboardEvent) {
      if (event.key === "Escape") setMobileRailOpen(false)
    }
    document.addEventListener("keydown", closeOnEscape)
    return () => document.removeEventListener("keydown", closeOnEscape)
  }, [mobileRailOpen])

  const sortedTodos = useMemo(
    () =>
      [...localTodos].sort((a, b) => {
        if (a.done !== b.done) return a.done ? 1 : -1
        return a.position - b.position
      }),
    [localTodos],
  )

  const projectSessions = useMemo(() => sessions, [sessions])
  const visibleProjectSessions = showAllSessions ? projectSessions : projectSessions.slice(0, 6)
  const activeGoalCount = sortedTodos.filter((todo) => !todo.done).length
  const doneGoalCount = sortedTodos.length - activeGoalCount
  const completionPercent = sortedTodos.length ? Math.round((doneGoalCount / sortedTodos.length) * 100) : 0
  const nextTodo = sortedTodos.find((todo) => !todo.done)
  const readySources = projectSources.filter(
    (source) => source.parse_status === "ready" && source.include_policy !== "exclude",
  )
  const excludedSources = projectSources.filter((source) => source.include_policy === "exclude")
  const parsingSources = projectSources.filter((source) => source.parse_status === "pending")
  const sourceTokens = readySources.reduce((sum, source) => sum + (source.token_estimate || 0), 0)
  const contextCapacityPercent = Math.min(
    100,
    Math.max(
      1,
      Math.round((localContext.length + projectMemories.length * 240 + sourceTokens * 3.8) / 1200),
    ),
  )
  const visiblePlanTodos = sortedTodos.slice(0, 8)
  const lastProjectSession = projectSessions[0]
  const openMilestones = sortedTodos.filter((todo) => !todo.done).slice(0, 3)
  const workspaceStatus =
    saving || savingMemory || sourceSaving || addingTask
      ? "Saving workspace"
      : loadingSessions || loadingMemories || loadingSources
        ? "Syncing project"
        : readySources.length > 0 || localContext.trim() || projectMemories.length > 0
          ? "Project context ready"
          : "Project needs context"

  const projectHealthRows = [
    {
      label: "Plan",
      value: sortedTodos.length ? `${activeGoalCount} active` : "No tasks",
      detail: nextTodo?.text || "Add the next concrete step.",
    },
    {
      label: "Sources",
      value: `${readySources.length} ready`,
      detail: excludedSources.length ? `${excludedSources.length} excluded from context` : "Included in project context.",
    },
    {
      label: "Memory",
      value: `${projectMemories.length} saved`,
      detail: "Project memory stays scoped to this workspace.",
    },
  ]

  const tabCounts: Partial<Record<ProjectWorkspaceTab, number>> = {
    conversations: projectSessions.length || project.session_count,
    memories: projectMemories.length,
    sources: projectSources.length,
    tasks: sortedTodos.length,
  }

  async function saveProject(fields?: Partial<Pick<Project, "name" | "description" | "context_md" | "color" | "pinned">>) {
    if (saving) return
    setSaving(true)
    setProjectNotice(null)
    try {
      const updated = await updateProject(project.id, {
        name: localName,
        description: localDescription,
        context_md: localContext,
        color: localColor,
        ...fields,
      })
      setLocalName(updated.name)
      setLocalDescription(updated.description)
      setLocalContext(updated.context_md)
      setLocalColor(updated.color)
      setLocalTodos(updated.todos)
      onUpdate(updated)
    } catch (error) {
      reportProjectNotice(
        "Project changes were not saved",
        error,
        () => void saveProject(fields),
      )
    } finally {
      setSaving(false)
    }
  }

  async function addTask(textOverride?: string) {
    const text = (textOverride ?? newTodoText).trim()
    if (!text) return
    setAddingTask(true)
    setProjectNotice(null)
    try {
      const todo = await addTodo(project.id, text)
      const nextTodos = [...localTodos, todo]
      if (!textOverride || newTodoText.trim() === text) setNewTodoText("")
      setLocalTodos(nextTodos)
      onUpdate(localProject(nextTodos))
    } catch (error) {
      reportProjectNotice(
        "Task was not added",
        error,
        () => void addTask(text),
      )
    } finally {
      setAddingTask(false)
    }
  }

  async function addProjectMemory(contentOverride?: string) {
    const content = (contentOverride ?? memoryDraft).trim()
    if (!content) return
    setSavingMemory(true)
    setProjectNotice(null)
    try {
      await addMemory(content, memoryType, project.id)
      if (!contentOverride || memoryDraft.trim() === content) setMemoryDraft("")
      await loadProjectMemories(project.id)
    } catch (error) {
      reportProjectNotice(
        "Memory was not captured",
        error,
        () => void addProjectMemory(content),
      )
    } finally {
      setSavingMemory(false)
    }
  }

  async function addProjectSource() {
    const content = sourceDraftContent.trim()
    const title = sourceDraftTitle.trim()
    if (!content) return
    setSourceSaving(true)
    setProjectNotice(null)
    try {
      await addProjectTextSource(project.id, {
        source_type: sourceDraftType,
        title,
        ...(sourceDraftType === "url" ? { url: content } : { content }),
      })
      setSourceDraftTitle("")
      setSourceDraftContent("")
      await loadProjectSources(project.id)
    } catch (error) {
      reportProjectNotice(
        "Project source was not added",
        error,
        () => void addProjectSource(),
      )
    } finally {
      setSourceSaving(false)
    }
  }

  async function toggleSourcePolicy(source: ProjectSource) {
    const nextPolicy = source.include_policy === "exclude" ? "include" : "exclude"
    setPendingSourceAction(`policy:${source.id}`)
    setProjectNotice(null)
    try {
      const updated = await updateProjectSource(project.id, source.id, {
        include_policy: nextPolicy,
      })
      setProjectSources((current) => current.map((item) => (item.id === source.id ? updated : item)))
      await loadProjectSources(project.id)
    } catch (error) {
      reportProjectNotice(
        "Source status was not saved",
        error,
        () => void toggleSourcePolicy(source),
      )
    } finally {
      setPendingSourceAction(null)
    }
  }

  async function removeSource(source: ProjectSource) {
    setPendingSourceAction(`delete:${source.id}`)
    setProjectNotice(null)
    try {
      await deleteProjectSource(project.id, source.id)
      setProjectSources((current) => current.filter((item) => item.id !== source.id))
      await loadProjectSources(project.id)
    } catch (error) {
      reportProjectNotice(
        "Source was not removed",
        error,
        () => void removeSource(source),
      )
    } finally {
      setPendingSourceAction(null)
    }
  }

  async function toggleTask(todoId: string) {
    const current = localTodos.find((todo) => todo.id === todoId)
    if (!current) return
    setPendingTodoAction(todoActionKey("toggle", todoId))
    setProjectNotice(null)
    try {
      const updatedTodo = await toggleTodo(project.id, todoId, !current.done)
      const nextTodos = localTodos.map((todo) =>
        todo.id === todoId ? updatedTodo ?? { ...todo, done: !todo.done } : todo,
      )
      setLocalTodos(nextTodos)
      onUpdate(localProject(nextTodos))
    } catch (error) {
      reportProjectNotice(
        "Task status was not saved",
        error,
        () => void toggleTask(todoId),
      )
    } finally {
      setPendingTodoAction(null)
    }
  }

  async function deleteTask(todoId: string) {
    setPendingTodoAction(todoActionKey("delete", todoId))
    setProjectNotice(null)
    try {
      await deleteTodo(project.id, todoId)
      const nextTodos = localTodos.filter((todo) => todo.id !== todoId)
      setLocalTodos(nextTodos)
      onUpdate(localProject(nextTodos))
    } catch (error) {
      reportProjectNotice(
        "Task was not deleted",
        error,
        () => void deleteTask(todoId),
      )
    } finally {
      setPendingTodoAction(null)
    }
  }

  async function commitTodoText(todoId: string) {
    const text = editingTodoText.trim()
    const current = localTodos.find((todo) => todo.id === todoId)
    if (!current || !text || text === current.text) {
      setEditingTodoId(null)
      return
    }
    setPendingTodoAction(todoActionKey("edit", todoId))
    setProjectNotice(null)
    try {
      const updatedTodo = await updateTodoText(project.id, todoId, text)
      const nextTodos = localTodos.map((todo) =>
        todo.id === todoId ? updatedTodo ?? { ...todo, text } : todo,
      )
      setLocalTodos(nextTodos)
      onUpdate(localProject(nextTodos))
      setEditingTodoId(null)
    } catch (error) {
      setEditingTodoId(todoId)
      setEditingTodoText(text)
      reportProjectNotice(
        "Task text was not saved",
        error,
        () => void commitTodoText(todoId),
      )
    } finally {
      setPendingTodoAction(null)
    }
  }

  function localProject(todos: Todo[]): Project {
    return {
      ...project,
      name: localName,
      description: localDescription,
      context_md: localContext,
      color: localColor,
      todos,
    }
  }

  function handleNewTodoKey(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      event.preventDefault()
      void addTask()
    }
  }

  function todoActionPending(action: TodoAction, todoId: string): boolean {
    return pendingTodoAction === todoActionKey(action, todoId)
  }

  async function handleArchiveProject() {
    setActionsOpen(false)
    setSaving(true)
    setProjectNotice(null)
    try {
      await archiveProject(project.id)
      onUpdate({ ...project, archived: true })
      onClose()
    } catch (error) {
      reportProjectNotice(
        "Project was not archived",
        error,
        () => void handleArchiveProject(),
      )
    } finally {
      setSaving(false)
    }
  }

  async function confirmDeleteProject() {
    setActionsOpen(false)
    setDeletingProject(true)
    setDeleteError(null)
    try {
      await deleteProject(project.id)
      onUpdate({ ...project, archived: true })
      onClose()
      setDeleteConfirmOpen(false)
    } catch (error) {
      setDeleteError(userFacingError(error))
    } finally {
      setDeletingProject(false)
    }
  }

  function renderProjectChats(limit = false) {
    const sessionsToRender = limit ? projectSessions.slice(0, 4) : visibleProjectSessions
    return (
      <div className="project-chat-list">
        {loadingSessions ? <p className="project-rail-loading">Loading project chats...</p> : null}
        {sessionsToRender.map((session) => (
          <button
            className="project-session-row"
            key={session.session_id}
            onClick={() => onOpenChat(project.id, session.session_id)}
            type="button"
          >
            <div className="min-w-0">
              <p>{sessionTitle(session)}</p>
              <span>{formatDate(session.updated_at || session.created_at || session.session_id)}</span>
            </div>
            <ExternalLink className="size-3.5" />
          </button>
        ))}
        {projectSessions.length === 0 ? (
          <p className="todo-empty">
            {project.session_count > 0 ? "Project chats will appear after refresh" : "No project chats yet"}
          </p>
        ) : null}
        {!limit && projectSessions.length > 6 ? (
          <button
            className="project-show-more"
            onClick={() => setShowAllSessions((value) => !value)}
            type="button"
          >
            {showAllSessions ? "Show fewer" : `Show ${projectSessions.length - 6} more`}
          </button>
        ) : null}
      </div>
    )
  }

  function renderProjectMemories(limit = false) {
    const memories = limit ? projectMemories.slice(0, 4) : projectMemories
    return (
      <div className={cn("project-memory-list", limit && "compact")}>
        {loadingMemories ? <p className="project-rail-loading">Loading project memory...</p> : null}
        {memories.map((memory) => (
          <div className="project-memory-card" key={memory.id}>
            <div className="project-memory-meta">
              <span className={cn("memory-type-badge", `type-${memory.type}`)}>{memory.type}</span>
              <span>{formatDate(memory.updated_at || memory.created_at)}</span>
            </div>
            <p>{memory.content || memory.name}</p>
          </div>
        ))}
        {projectMemories.length === 0 ? (
          <p className="todo-empty">No project memories yet. Capture decisions, sources, and formulas here.</p>
        ) : null}
      </div>
    )
  }

  function renderTaskList(limit = false) {
    const todos = limit ? sortedTodos.slice(0, 4) : visiblePlanTodos
    return (
      <div className="project-plan-list">
        {todos.map((todo, index) => (
          <div
            className={cn(
              "project-plan-row",
              todo.done && "done",
              pendingTodoAction?.endsWith(`:${todo.id}`) && "pending",
            )}
            key={todo.id}
          >
            <button
              className="project-plan-check"
              disabled={Boolean(pendingTodoAction)}
              onClick={() => void toggleTask(todo.id)}
              type="button"
            >
              {todoActionPending("toggle", todo.id) ? (
                <RotateCcw className="size-3.5 animate-spin" />
              ) : todo.done ? (
                <Check className="size-3.5" />
              ) : (
                <span>{String(index + 1).padStart(2, "0")}</span>
              )}
            </button>
            {editingTodoId === todo.id ? (
              <input
                autoFocus
                className="todo-edit-input"
                disabled={todoActionPending("edit", todo.id)}
                onBlur={() => void commitTodoText(todo.id)}
                onChange={(event) => setEditingTodoText(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") void commitTodoText(todo.id)
                  if (event.key === "Escape") setEditingTodoId(null)
                }}
                value={editingTodoText}
              />
            ) : (
              <button
                className="project-plan-text"
                disabled={Boolean(pendingTodoAction)}
                onClick={() => {
                  setEditingTodoId(todo.id)
                  setEditingTodoText(todo.text)
                }}
                type="button"
              >
                {todo.text}
                <span className="project-plan-status">
                  {todo.done ? "Done" : index === 0 ? "Now" : "Queued"}
                </span>
              </button>
            )}
            <button
              aria-label="Delete task"
              className="todo-delete"
              disabled={Boolean(pendingTodoAction)}
              onClick={() => void deleteTask(todo.id)}
              type="button"
            >
              {todoActionPending("delete", todo.id) ? (
                <RotateCcw className="size-3.5 animate-spin" />
              ) : (
                <X className="size-3.5" />
              )}
            </button>
          </div>
        ))}
        {sortedTodos.length === 0 ? (
          <p className="todo-empty">No tasks yet. Add the next concrete move and Geneva will keep it in view.</p>
        ) : null}
      </div>
    )
  }

  return (
    <div className="project-view">
      <header className="project-view-header">
        <Button className="gap-2" onClick={onClose} variant="quiet">
          <ArrowLeft className="size-4" />
          Back to Chat
        </Button>
        <div className="project-view-title">
          <Folder className="size-4" style={{ color: localColor }} />
          <span>{localName || "Untitled project"}</span>
        </div>
        <div className="project-header-actions">
          <Button className="project-new-chat-button gap-2" onClick={() => onOpenChat(project.id)} variant="default">
            <Plus className="size-4" />
            <span className="project-action-label">New Chat</span>
          </Button>
          <Button
            aria-label="Edit project info"
            onClick={() => setInfoOpen(true)}
            size="compactIcon"
            variant="quiet"
          >
            <Pencil className="size-4" />
          </Button>
          <div className="project-actions-wrap">
            <Button
              aria-label="Project actions"
              onClick={() => setActionsOpen((open) => !open)}
              size="compactIcon"
              variant="quiet"
            >
              <MoreVertical className="size-4" />
            </Button>
            {actionsOpen ? (
              <div className="project-actions-menu">
                <button
                  onClick={() => {
                    setActionsOpen(false)
                    void saveProject({ pinned: !project.pinned })
                  }}
                  type="button"
                >
                  {project.pinned ? "Unpin project" : "Pin project"}
                </button>
                <button onClick={() => void handleArchiveProject()} type="button">
                  Archive project
                </button>
                <button
                  className="danger"
                  onClick={() => {
                    setActionsOpen(false)
                    setDeleteConfirmOpen(true)
                  }}
                  type="button"
                >
                  Delete project
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </header>

      <main className="project-workspace project-workspace-polished">
        <div className="project-claude-layout project-claude-layout-v2">
          <section className="project-main-column">
            <div className="project-topline">
              <button className="project-breadcrumb" onClick={onClose} type="button">
                <ArrowLeft className="size-4" />
                All projects
              </button>
              <div className="project-topline-actions" aria-label="Project quick actions">
                <button
                  aria-label="Pin project"
                  disabled={saving}
                  onClick={() => void saveProject({ pinned: !project.pinned })}
                  type="button"
                >
                  <Pin className={cn("size-4", project.pinned && "active")} />
                </button>
              </div>
            </div>

            {projectNotice ? (
              <ProjectNoticeBanner
                notice={projectNotice}
                onDismiss={() => setProjectNotice(null)}
              />
            ) : null}

            <section className="project-hero-panel project-health">
              <span className="project-command-eyebrow">
                <Activity className="size-3.5" />
                Project health
              </span>
              <h1>{localName || "Untitled project"}</h1>
              <p>{localDescription || "A focused workspace where every chat, task, memory, instruction, and source stays scoped to this project."}</p>
              <div className="project-state-line">
                <span className={cn((saving || savingMemory || sourceSaving || addingTask || loadingSessions || loadingMemories || loadingSources) && "syncing")} />
                {workspaceStatus}
              </div>
              <div className="project-signal-grid" aria-label="Project status">
                <div>
                  <strong>{completionPercent}%</strong>
                  <span>Progress</span>
                </div>
                <div>
                  <strong>{projectMemories.length}</strong>
                  <span>Memories</span>
                </div>
                <div>
                  <strong>{readySources.length}</strong>
                  <span>Sources</span>
                </div>
                <div>
                  <strong>{projectSessions.length || project.session_count}</strong>
                  <span>Chats</span>
                </div>
              </div>
            </section>

            <button
              aria-controls="project-context-sheet"
              aria-expanded={mobileRailOpen}
              aria-label="Open project context"
              className="project-mobile-context-toggle ui8-overflow-safe"
              onClick={() => setMobileRailOpen(true)}
              type="button"
            >
              <BookOpenCheck className="size-4" />
              <span>
                <strong>Project context</strong>
                <small>{readySources.length} sources · {projectMemories.length} memories · {activeGoalCount} active</small>
              </span>
            </button>

            <nav aria-label="Project workspace tabs" className="project-tabs">
              {PROJECT_WORKSPACE_TABS.map((tab) => (
                <button
                  aria-pressed={activeTab === tab.id}
                  className={cn("project-tab", activeTab === tab.id && "active")}
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  type="button"
                >
                  <span>{tab.label}</span>
                  {tabCounts[tab.id] !== undefined ? <small>{tabCounts[tab.id]}</small> : null}
                </button>
              ))}
            </nav>

            <section className="project-tab-panel">
              {activeTab === "overview" ? (
                <>
                  <button className="project-launch-composer" onClick={() => onOpenChat(project.id)} type="button">
                    <span>How can I help with {localName || "this project"}?</span>
                    <span>
                      <Plus className="size-4" />
                      Start with project context
                    </span>
                  </button>

                  <section className="project-section-block">
                    <div className="project-section-heading">
                      <div>
                        <h2>Project health</h2>
                        <p>Context, plan, and memory signals Geneva will use before the next chat.</p>
                      </div>
                      <ShieldCheck className="size-4" />
                    </div>
                    <div className="project-health-list">
                      {projectHealthRows.map((row) => (
                        <div className="project-health-row" key={row.label}>
                          <span>{row.label}</span>
                          <strong>{row.value}</strong>
                          <p>{row.detail}</p>
                        </div>
                      ))}
                    </div>
                  </section>

                  <section className="project-section-block">
                    <div className="project-section-heading">
                      <div>
                        <h2>Project plan</h2>
                        <p>Small, visible steps keep the workspace actionable.</p>
                      </div>
                      <ListChecks className="size-4" />
                    </div>
                    <div className="project-run-preview" aria-label="Project execution plan">
                      <div className="project-run-card now">
                        <span>Now</span>
                        <p>{openMilestones[0]?.text || "Add a concrete next step in Tasks."}</p>
                      </div>
                      <div className="project-run-card">
                        <span>Next</span>
                        <p>{openMilestones[1]?.text || "Future steps will stay queued here."}</p>
                      </div>
                      <div className="project-run-card done">
                        <span>Done</span>
                        <p>{doneGoalCount} completed · {activeGoalCount} still active</p>
                      </div>
                    </div>
                  </section>

                  <div className="project-overview-split">
                    <section className="project-section-block">
                      <div className="project-section-heading">
                        <div>
                          <h2>Recent conversations</h2>
                          <p>Chats attached to this project boundary.</p>
                        </div>
                        <MessageSquare className="size-4" />
                      </div>
                      {renderProjectChats(true)}
                    </section>

                    <section className="project-section-block">
                      <div className="project-section-heading">
                        <div>
                          <h2>Ready sources</h2>
                          <p>{readySources.length} included · {parsingSources.length} parsing</p>
                        </div>
                        <Database className="size-4" />
                      </div>
                      <div className="project-source-mini-list">
                        {readySources.slice(0, 4).map((source) => (
                          <div className="project-source-mini" key={source.id}>
                            <span className={cn("project-source-status", sourceStatusClass(source))}>
                              {sourceStatusLabel(source)}
                            </span>
                            <p>{source.title}</p>
                          </div>
                        ))}
                        {readySources.length === 0 ? (
                          <p className="todo-empty">No ready sources yet. Add text, markdown, or a URL in Sources.</p>
                        ) : null}
                      </div>
                    </section>
                  </div>
                </>
              ) : null}

              {activeTab === "conversations" ? (
                <section className="project-section-block full">
                  <div className="project-section-heading">
                    <div>
                      <h2>Conversations</h2>
                      <p>Every attached conversation reuses this project context and memory.</p>
                    </div>
                    <Button className="gap-2" onClick={() => onOpenChat(project.id)}>
                      <Plus className="size-4" />
                      New Chat
                    </Button>
                  </div>
                  {renderProjectChats()}
                </section>
              ) : null}

              {activeTab === "memories" ? (
                <section className="project-section-block full">
                  <div className="project-section-heading">
                    <div>
                      <h2>Memories</h2>
                      <p>Project memory stays scoped to this workspace. Personal memory remains separate unless explicitly saved.</p>
                    </div>
                    <span className="project-privacy-pill">
                      <LockKeyhole className="size-3.5" />
                      Only you
                    </span>
                  </div>
                  <div className="project-memory-capture project-memory-capture-wide">
                    <textarea
                      className="project-memory-input"
                      onChange={(event) => setMemoryDraft(event.target.value)}
                      placeholder="Capture a source, decision, formula, question, or finding..."
                      rows={4}
                      value={memoryDraft}
                    />
                    <div className="project-memory-actions">
                      <select onChange={(event) => setMemoryType(event.target.value)} value={memoryType}>
                        {PROJECT_MEMORY_TYPES.map((type) => (
                          <option key={type.value} value={type.value}>
                            {type.label}
                          </option>
                        ))}
                      </select>
                      <Button
                        disabled={!memoryDraft.trim() || savingMemory}
                        onClick={() => void addProjectMemory()}
                        type="button"
                      >
                        {savingMemory ? "Saving..." : "Capture"}
                      </Button>
                    </div>
                  </div>
                  {renderProjectMemories()}
                </section>
              ) : null}

              {activeTab === "sources" ? (
                <section className="project-section-block full">
                  <div className="project-section-heading">
                    <div>
                      <h2>Sources</h2>
                      <p>Ready sources are included in project chats. Excluded sources stay attached but out of context.</p>
                    </div>
                    <Database className="size-4" />
                  </div>

                  <div className="project-source-add">
                    <div className="project-source-type-row">
                      <select
                        aria-label="Source type"
                        onChange={(event) => setSourceDraftType(event.target.value as ProjectSourceDraftType)}
                        value={sourceDraftType}
                      >
                        <option value="text">Text</option>
                        <option value="markdown">Markdown</option>
                        <option value="url">URL</option>
                      </select>
                      <input
                        className="project-input"
                        onChange={(event) => setSourceDraftTitle(event.target.value)}
                        placeholder="Source title"
                        value={sourceDraftTitle}
                      />
                    </div>
                    <textarea
                      className="project-textarea project-source-input"
                      onChange={(event) => setSourceDraftContent(event.target.value)}
                      placeholder={sourceDraftType === "url" ? "https://..." : "Paste project source content..."}
                      rows={sourceDraftType === "url" ? 2 : 6}
                      value={sourceDraftContent}
                    />
                    <div className="project-source-add-actions">
                      <p>PDF and DOCX parsing is supported by the backend; browser file upload UI will land after this workspace pass.</p>
                      <Button disabled={!sourceDraftContent.trim() || sourceSaving} onClick={() => void addProjectSource()}>
                        {sourceSaving ? "Adding..." : "Add source"}
                      </Button>
                    </div>
                  </div>

                  <div className="project-source-list">
                    {loadingSources ? <p className="project-rail-loading">Loading project sources...</p> : null}
                    {projectSources.map((source) => (
                      <div className="project-source-row" key={source.id}>
                        <div className="project-source-main">
                          <div className="project-source-title-row">
                            <FileText className="size-4" />
                            <strong>{source.title || "Untitled source"}</strong>
                            <span className={cn("project-source-status", sourceStatusClass(source))}>
                              {sourceStatusLabel(source)}
                            </span>
                            <span className="project-source-kind">{sourceTypeLabel(source)}</span>
                          </div>
                          <p>
                            {source.uri || `${source.token_estimate || 0} estimated tokens`}
                            {source.parse_error ? ` · ${source.parse_error}` : ""}
                          </p>
                        </div>
                        <div className="project-source-actions">
                          <button
                            disabled={Boolean(pendingSourceAction)}
                            onClick={() => void toggleSourcePolicy(source)}
                            type="button"
                          >
                            {pendingSourceAction === `policy:${source.id}` ? "Saving..." : source.include_policy === "exclude" ? "Include" : "Exclude"}
                          </button>
                          <button
                            disabled={Boolean(pendingSourceAction)}
                            onClick={() => void removeSource(source)}
                            type="button"
                          >
                            {pendingSourceAction === `delete:${source.id}` ? "Removing..." : "Remove"}
                          </button>
                        </div>
                      </div>
                    ))}
                    {projectSources.length === 0 ? (
                      <p className="todo-empty">No project sources yet. Add the files, text, or URLs Geneva should treat as project knowledge.</p>
                    ) : null}
                  </div>

                  <div className="project-source-preview">
                    <div className="project-section-heading compact">
                      <div>
                        <h2>Context preview</h2>
                        <p>{sourcePreview?.count ?? 0} ready sources will be injected before project turns.</p>
                      </div>
                      <Sparkles className="size-4" />
                    </div>
                    <pre>{sourcePreview?.preview || "No ready project source context yet."}</pre>
                  </div>
                </section>
              ) : null}

              {activeTab === "tasks" ? (
                <section className="project-section-block full">
                  <div className="project-section-heading">
                    <div>
                      <h2>Project plan</h2>
                      <p>Tasks are the visible plan Geneva follows while working inside this project.</p>
                    </div>
                    <ListChecks className="size-4" />
                  </div>
                  <div className="todo-add-row project-task-add">
                    <input
                      className="project-input"
                      onChange={(event) => setNewTodoText(event.target.value)}
                      onKeyDown={handleNewTodoKey}
                      placeholder="Add next step..."
                      value={newTodoText}
                    />
                    <Button
                      aria-label="Add task"
                      disabled={!newTodoText.trim() || addingTask}
                      onClick={() => void addTask()}
                      size="compactIcon"
                    >
                      {addingTask ? <RotateCcw className="size-4 animate-spin" /> : <Plus className="size-4" />}
                    </Button>
                  </div>
                  {renderTaskList()}
                </section>
              ) : null}

              {activeTab === "artifacts" ? (
                <section className="project-section-block full">
                  <div className="project-section-heading">
                    <div>
                      <h2>Artifacts</h2>
                      <p>Deep Research reports saved while this project is attached stay here with their source trace.</p>
                    </div>
                    <Layers className="size-4" />
                  </div>
                  <ProjectArtifactsPanel projectId={project.id} projectName={localName} />
                </section>
              ) : null}

              {activeTab === "settings" ? (
                <section className="project-section-block full">
                  <div className="project-section-heading">
                    <div>
                      <h2>Settings</h2>
                      <p>Project instructions are separate from sources and memory.</p>
                    </div>
                    <Settings2 className="size-4" />
                  </div>
                  <div className="project-settings-list">
                    <div className="project-settings-row">
                      <div>
                        <strong>Instructions</strong>
                        <p>{localContext.trim() || "No project instructions yet."}</p>
                      </div>
                      <Button onClick={() => setInfoOpen(true)} variant="quiet">
                        Edit
                      </Button>
                    </div>
                    <div className="project-settings-row">
                      <div>
                        <strong>Memory boundary</strong>
                        <p>Project memory stays scoped to this workspace. Personal memory remains separate unless explicitly saved.</p>
                      </div>
                      <span className="project-privacy-pill">
                        <LockKeyhole className="size-3.5" />
                        Only you
                      </span>
                    </div>
                    <div className="project-settings-row">
                      <div>
                        <strong>Project color</strong>
                        <p>Used in the sidebar, composer project chip, and workspace identity.</p>
                      </div>
                      <span className="project-color-preview" style={{ background: localColor }} />
                    </div>
                  </div>
                </section>
              ) : null}
            </section>
          </section>

          {mobileRailOpen ? (
            <button
              aria-label="Close project context overlay"
              className="project-context-sheet-backdrop"
              onClick={() => setMobileRailOpen(false)}
              type="button"
            />
          ) : null}

          <aside
            aria-label="Project context panel"
            className={cn(
              "project-side-panel project-command-rail project-context-mobile-sheet mobile-bottom-sheet",
              mobileRailOpen && "open",
            )}
            id="project-context-sheet"
          >
            <div className="project-mobile-context-sheet-header">
              <div>
                <span>Project context</span>
                <strong>{completionPercent}% ready</strong>
              </div>
              <button aria-label="Close project context" onClick={() => setMobileRailOpen(false)} type="button">
                <X className="size-4" />
              </button>
            </div>
            <section className="project-side-section project-progress-section">
              <div className="project-rail-header">
                <div>
                  <span>Project health</span>
                  <h2>{completionPercent}% ready</h2>
                  <p>{activeGoalCount} active · {doneGoalCount} done</p>
                </div>
                <div className="project-progress-orb" aria-label={`${completionPercent}% complete`}>
                  {completionPercent}%
                </div>
              </div>
              <div className="project-progress-track">
                <span style={{ width: `${completionPercent}%` }} />
              </div>
              <div className="project-next-step-card">
                <ListChecks className="size-4" />
                <div>
                  <span>Next step</span>
                  <p>{nextTodo?.text || "Add the next concrete task so Geneva has a visible plan."}</p>
                </div>
              </div>
            </section>

            <section className="project-side-section">
              <div className="project-section-heading compact">
                <div>
                  <h2>Project context</h2>
                  <p>{contextCapacityPercent}% estimated context capacity used</p>
                </div>
                <BookOpenCheck className="size-4" />
              </div>
              <div className="project-progress-track subtle">
                <span style={{ width: `${contextCapacityPercent}%` }} />
              </div>
              <div className="project-context-summary">
                <div>
                  <Database className="size-4" />
                  <span>{readySources.length} ready sources</span>
                </div>
                <div>
                  <BookOpenCheck className="size-4" />
                  <span>{projectMemories.length} project memories</span>
                </div>
                <div>
                  <FileText className="size-4" />
                  <span>{localContext.trim() ? "Instructions set" : "No instructions yet"}</span>
                </div>
              </div>
              <div className="project-context-footnote">
                Last project chat: {lastProjectSession ? formatDate(lastProjectSession.updated_at || lastProjectSession.created_at) : "none yet"}
              </div>
            </section>

            <section className="project-side-section project-rail-memory-capture">
              <div className="project-section-heading compact">
                <div>
                  <h2>Capture memory</h2>
                  <p>Save a project-scoped note without leaving the rail.</p>
                </div>
                <Brain className="size-4" />
              </div>
              <div className="project-memory-capture project-memory-capture-rail">
                <textarea
                  className="project-memory-input"
                  onChange={(event) => setMemoryDraft(event.target.value)}
                  placeholder="Decision, source, formula, or question..."
                  rows={3}
                  value={memoryDraft}
                />
                <div className="project-memory-actions">
                  <select onChange={(event) => setMemoryType(event.target.value)} value={memoryType}>
                    {PROJECT_MEMORY_TYPES.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                  <Button
                    disabled={!memoryDraft.trim() || savingMemory}
                    onClick={() => void addProjectMemory()}
                    type="button"
                    variant="subtle"
                  >
                    {savingMemory ? "Saving..." : "Capture"}
                  </Button>
                </div>
              </div>
            </section>

            <section className="project-side-section">
              <div className="project-section-heading compact">
                <div>
                  <h2>Project plan</h2>
                  <p>{activeGoalCount} active steps</p>
                </div>
                <button className="project-mini-action" onClick={() => setActiveTab("tasks")} type="button">
                  <Plus className="size-4" />
                </button>
              </div>
              {renderTaskList(true)}
            </section>

            <section className="project-side-section">
              <div className="project-section-heading compact">
                <div>
                  <h2>Privacy</h2>
                  <p>Only you can see this project workspace.</p>
                </div>
                <span className="project-privacy-pill">
                  <LockKeyhole className="size-3.5" />
                  Only you
                </span>
              </div>
            </section>
          </aside>
        </div>
      </main>

      {infoOpen ? (
        <ProjectInfoModal
          localColor={localColor}
          localContext={localContext}
          localDescription={localDescription}
          localName={localName}
          onClose={() => setInfoOpen(false)}
          onSave={(fields) => void saveProject(fields)}
          onSetColor={setLocalColor}
          onSetContext={setLocalContext}
          onSetDescription={setLocalDescription}
          onSetName={setLocalName}
          saving={saving}
        />
      ) : null}

      {deleteConfirmOpen ? (
        <ProjectDeleteModal
          deleteError={deleteError}
          deletingProject={deletingProject}
          localName={localName}
          onClose={() => setDeleteConfirmOpen(false)}
          onConfirm={() => void confirmDeleteProject()}
        />
      ) : null}
    </div>
  )
}
