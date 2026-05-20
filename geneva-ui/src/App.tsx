import { Suspense, lazy, useCallback, useEffect, useMemo, useRef, useState } from "react"

import { AppShell } from "@/components/AppShell"
import { ChatCanvas } from "@/components/ChatCanvas"
import { Composer } from "@/components/Composer"
import { CustomizeSurface } from "@/components/CustomizeSurface"
import { OpenSourceModal } from "@/components/OpenSourceModal"
import { SearchOverlay } from "@/components/SearchOverlay"
import { Sidebar } from "@/components/Sidebar"
import { ToolPermissionModal } from "@/components/ToolPermissionModal"
import { ViewLoading } from "@/components/ViewLoading"
import { TRUSTED_REQUEST_HEADER } from "@/lib/api/core"
import {
  amendConversation,
  associateSession,
  addMemory,
  addSessionToProject,
  emptyMemoryStats,
  executeCommand,
  fetchCommands,
  fetchConversationTitle,
  fetchMemoryStats,
  fetchProject,
  fetchProjects,
  fetchSettings,
  attachTracesToMessages,
  fetchSkills,
  fetchSessionMessages,
  fetchSessionTraces,
  fetchSessions,
  generateConversationTitle,
  getActiveSessionId,
  pinSession,
  resolveToolPermission,
  saveConversationTitle,
  setActiveSessionId,
  streamChat,
  streamResearch,
  undoMemoryWriteEvent,
  updateResearchRunStatus,
} from "@/lib/api"
import { fetchResearchPlan } from "@/lib/api/research-api"

import type {
  Attachment,
  ChatMessage,
  ContextDisclosureSummary,
  MemoryStats,
  MemoryWriteEvent,
  Project,
  ResearchProgressItem,
  SessionSummary,
  SkillInvocationScope,
  SkillMeta,
  SlashCommand,
  ToolPermissionRequest,
} from "@/types"
import type { ImagePayload } from "@/lib/api"
import {
  activityFromStreamEvent,
  friendlyErrorMessage,
  mergeActivityEvent,
  mergeToolTrace,
  projectDataErrorMessage,
  statusTextForStreamEvent,
  traceFromStreamEvent,
} from "@/lib/agent-events"
import {
  buildAugmentedMessage,
  buildBranchedTurnMessage,
  buildBranchTranscript,
  buildDisplayMessage,
  buildTurnMessage,
  cleanMessageForDraft,
  dedupeCommands,
  detectProjectFromMessage,
  findMatchingCommand,
  formatContextCommandOutput,
} from "@/lib/chat-message"
import {
  GHOST_MODE_KEY,
  THEME_MODE_KEY,
  THEME_MODE_USER_SET_KEY,
  getInitialThemeMode,
  getSystemDarkMode,
  type ThemeMode,
} from "@/lib/theme"

type ActiveTab = "chat" | "skill"
type ComposerModeId = "low" | "medium" | "high" | "extra_high"
type TurnOptions = { webSearch?: boolean; modeId?: string; skillScope?: SkillInvocationScope }
const SIDEBAR_COLLAPSED_KEY = "geneva.sidebarCollapsed"

function normalizeComposerMode(modeId: string | null | undefined): ComposerModeId {
  const normalized = String(modeId ?? "").trim().toLowerCase().replace(/[-\s]+/g, "_")
  if (normalized === "low" || normalized === "medium" || normalized === "high" || normalized === "extra_high") {
    return normalized
  }
  return "medium"
}

function attachmentsToImages(attachments: Attachment[]): ImagePayload[] {
  return attachments
    .filter((attachment) => attachment.type === "image" && attachment.dataUrl)
    .map((attachment) => {
      const dataUrl = attachment.dataUrl!
      const match = /^data:(image\/[a-z]+);base64,(.+)$/.exec(dataUrl)
      if (!match) return null
      return {
        type: "base64" as const,
        media_type: match[1] as ImagePayload["media_type"],
        data: match[2],
      }
    })
    .filter((image): image is ImagePayload => image !== null)
}

function memoryWriteEventFromPayload(value: unknown): MemoryWriteEvent | null {
  if (!value || typeof value !== "object") return null
  const record = value as Record<string, unknown>
  if (typeof record.id !== "string" || typeof record.memory_id !== "string") return null
  if (typeof record.user_visible_text !== "string" || typeof record.status !== "string") return null
  return {
    id: record.id,
    memory_id: record.memory_id,
    session_id: typeof record.session_id === "string" ? record.session_id : null,
    turn_id: typeof record.turn_id === "string" ? record.turn_id : null,
    project_id: typeof record.project_id === "string" ? record.project_id : null,
    write_type: typeof record.write_type === "string" ? record.write_type : "auto_saved",
    confidence: typeof record.confidence === "number" ? record.confidence : null,
    sensitivity: typeof record.sensitivity === "string" ? record.sensitivity : null,
    user_visible_text: record.user_visible_text,
    source_excerpt: typeof record.source_excerpt === "string" ? record.source_excerpt : null,
    status: record.status,
    created_at: typeof record.created_at === "string" ? record.created_at : new Date().toISOString(),
    updated_at: typeof record.updated_at === "string" ? record.updated_at : null,
  }
}

function contextSummaryFromPayload(value: unknown): ContextDisclosureSummary | null {
  if (!value || typeof value !== "object") return null
  const record = value as Record<string, unknown>
  if (typeof record.summary !== "string" || !record.summary.trim()) return null
  const counts = record.counts && typeof record.counts === "object"
    ? (record.counts as ContextDisclosureSummary["counts"])
    : {}
  return {
    session_id: typeof record.session_id === "string" ? record.session_id : null,
    turn_id: typeof record.turn_id === "string" ? record.turn_id : null,
    ledger_id: typeof record.ledger_id === "string" ? record.ledger_id : null,
    summary: record.summary,
    counts,
    projects: Array.isArray(record.projects) ? record.projects.filter((item): item is string => typeof item === "string") : [],
    skills: Array.isArray(record.skills) ? record.skills.filter((item): item is string => typeof item === "string") : [],
    tools: Array.isArray(record.tools) ? record.tools.filter((item): item is string => typeof item === "string") : [],
    mode: record.mode && typeof record.mode === "object"
      ? (record.mode as ContextDisclosureSummary["mode"])
      : null,
    mode_id: typeof record.mode_id === "string" ? record.mode_id : null,
    mode_label: typeof record.mode_label === "string" ? record.mode_label : null,
    route_reason: typeof record.route_reason === "string" ? record.route_reason : null,
    cost_tier: typeof record.cost_tier === "string" ? record.cost_tier : null,
    model: typeof record.model === "string" ? record.model : null,
    ghost_mode: Boolean(record.ghost_mode),
    no_memory_write: Boolean(record.no_memory_write),
    trimmed: Boolean(record.trimmed),
    budget: record.budget && typeof record.budget === "object" ? (record.budget as Record<string, unknown>) : {},
    created_at: typeof record.created_at === "string" ? record.created_at : null,
  }
}

function isAbortError(error: unknown): boolean {
  if (error instanceof DOMException && error.name === "AbortError") return true
  if (error && typeof error === "object" && "name" in error) {
    return String((error as { name?: unknown }).name) === "AbortError"
  }
  return false
}

function mergeResearchProgress(
  current: ResearchProgressItem[] | undefined,
  next: ResearchProgressItem,
): ResearchProgressItem[] {
  const existing = current ?? []
  const index = existing.findIndex((item) => item.step === next.step && item.label === next.label)
  if (index >= 0) {
    return existing.map((item, itemIndex) => (itemIndex === index ? next : item))
  }
  return [...existing, next].slice(-8)
}

const MemoryPanel = lazy(() =>
  import("@/components/MemoryPanel").then((module) => ({ default: module.MemoryPanel })),
)
const ArtifactsSurface = lazy(() =>
  import("@/components/ArtifactsSurface").then((module) => ({ default: module.ArtifactsSurface })),
)
const NewProjectModal = lazy(() =>
  import("@/components/NewProjectModal").then((module) => ({ default: module.NewProjectModal })),
)
const ProjectView = lazy(() =>
  import("@/components/ProjectView").then((module) => ({ default: module.ProjectView })),
)
const Settings = lazy(() =>
  import("@/components/Settings").then((module) => ({ default: module.Settings })),
)

function App() {
  const [memoryOpen, setMemoryOpen] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(() => getActiveSessionId())
  const [addToProjectSessionId, setAddToProjectSessionId] = useState<string | null>(null)
  const [sessionTitle, setSessionTitle] = useState<string | null>(null)
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [memoryStats, setMemoryStats] = useState<MemoryStats>(emptyMemoryStats)
  const [commands, setCommands] = useState<SlashCommand[]>([])
  const [skills, setSkills] = useState<SkillMeta[]>([])
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState("")
  const [branchContext, setBranchContext] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [statusText, setStatusText] = useState<string | null>(null)
  const [researchMode, setResearchMode] = useState(false)
  const [composerModeId, setComposerModeId] = useState<ComposerModeId>("medium")
  const pendingAutoSendRef = useRef<string | null>(null)
  const activeChatAbortRef = useRef<AbortController | null>(null)
  const activeResearchAbortRef = useRef<AbortController | null>(null)
  const currentStreamSessionIdRef = useRef<string | null>(sessionId)
  const [activeTab, setActiveTab] = useState<ActiveTab>("chat")
  const [showSettings, setShowSettings] = useState(false)
  const [showOpenSource, setShowOpenSource] = useState(false)
  const [showArtifacts, setShowArtifacts] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => getInitialThemeMode())
  const [systemDark, setSystemDark] = useState(() => getSystemDarkMode())
  const [ghostMode, setGhostMode] = useState(() => localStorage.getItem(GHOST_MODE_KEY) === "1")
  const [sidebarCollapsed, setSidebarCollapsed] = useState(
    () => localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "1",
  )
  const [mobileLayout, setMobileLayout] = useState(
    () => window.matchMedia?.("(max-width: 760px)").matches ?? false,
  )
  const [projects, setProjects] = useState<Project[]>([])
  const [projectsLoading, setProjectsLoading] = useState(false)
  const [projectsError, setProjectsError] = useState<string | null>(null)
  const [activeProject, setActiveProject] = useState<Project | null>(null)
  const [memoryWriteNotice, setMemoryWriteNotice] = useState<MemoryWriteEvent | null>(null)
  const [showProjectView, setShowProjectView] = useState(false)
  const [viewingProject, setViewingProject] = useState<Project | null>(null)
  const [showNewProjectModal, setShowNewProjectModal] = useState(false)
  const [permissionRequest, setPermissionRequest] = useState<ToolPermissionRequest | null>(null)
  const pendingQueueRef = useRef<
    Array<{ text: string; attachments: Attachment[]; options?: TurnOptions }>
  >([])

  const effectiveDarkMode = themeMode === "system" ? systemDark : themeMode === "dark"
  const effectiveSidebarCollapsed = sidebarCollapsed && !mobileLayout
  const isStreaming = useMemo(() => {
    const lastMessage = messages[messages.length - 1]
    return Boolean(lastMessage?.role === "assistant" && lastMessage.loading)
  }, [messages])

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)")
    const handleChange = () => setSystemDark(media.matches)
    handleChange()
    if (typeof media.addEventListener === "function") {
      media.addEventListener("change", handleChange)
      return () => media.removeEventListener("change", handleChange)
    }
    media.addListener(handleChange)
    return () => media.removeListener(handleChange)
  }, [])

  useEffect(() => {
    const media = window.matchMedia("(max-width: 760px)")
    const handleChange = () => setMobileLayout(media.matches)
    handleChange()
    if (typeof media.addEventListener === "function") {
      media.addEventListener("change", handleChange)
      return () => media.removeEventListener("change", handleChange)
    }
    media.addListener(handleChange)
    return () => media.removeListener(handleChange)
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle("dark", effectiveDarkMode)
    document.documentElement.dataset.themeMode = themeMode
    localStorage.setItem(THEME_MODE_KEY, themeMode)
  }, [effectiveDarkMode, themeMode])

  useEffect(() => {
    localStorage.setItem(GHOST_MODE_KEY, ghostMode ? "1" : "0")
  }, [ghostMode])

  const handleThemeModeChange = useCallback((mode: ThemeMode) => {
    localStorage.setItem(THEME_MODE_USER_SET_KEY, "1")
    setThemeMode(mode)
  }, [])

  useEffect(() => {
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, sidebarCollapsed ? "1" : "0")
  }, [sidebarCollapsed])

  const refreshMemory = useCallback(async () => {
    try {
      setMemoryStats(await fetchMemoryStats(sessionId))
    } catch {
      setMemoryStats((current) => current)
    }
  }, [sessionId])

  const refreshSessions = useCallback(async () => {
    try {
      setSessions(await fetchSessions())
    } catch {
      setSessions([])
    }
  }, [])

  const refreshProjects = useCallback(async () => {
    setProjectsLoading(true)
    try {
      const nextProjects = await fetchProjects()
      setProjects(nextProjects)
      setProjectsError(null)
    } catch (error) {
      setProjectsError(projectDataErrorMessage(error))
    } finally {
      setProjectsLoading(false)
    }
  }, [])

  const refreshSkills = useCallback(async () => {
    try {
      const result = await fetchSkills()
      setSkills(result.skills)
    } catch {
      setSkills([])
    }
  }, [])

  useEffect(() => {
    void fetchCommands().then(setCommands).catch(() => setCommands([]))
    void fetchSettings()
      .then((settings) => setComposerModeId(normalizeComposerMode(settings.config.default_mode)))
      .catch(() => undefined)
    void refreshSkills()
    void refreshSessions()
    void refreshProjects()
    const savedSessionId = getActiveSessionId()
    if (savedSessionId) {
      void fetchSessionMessages(savedSessionId)
        .then(setMessages)
        .catch(() => setMessages([]))
    }
  }, [refreshProjects, refreshSessions, refreshSkills])

  useEffect(() => {
    if (activeProject) {
      const updated = projects.find((project) => project.id === activeProject.id)
      if (updated) setActiveProject(updated)
    }
    if (viewingProject) {
      const updated = projects.find((project) => project.id === viewingProject.id)
      if (updated) setViewingProject(updated)
    }
  }, [activeProject, projects, viewingProject])

  useEffect(() => {
    if (!sessionId) {
      setSessionTitle(null)
      return
    }
    void fetchConversationTitle(sessionId)
      .then((title) => setSessionTitle(title || null))
      .catch(() => setSessionTitle(null))
  }, [sessionId])

  useEffect(() => {
    void refreshMemory()
    const interval = window.setInterval(() => void refreshMemory(), 30000)
    return () => window.clearInterval(interval)
  }, [refreshMemory])

  const allCommands = useMemo(
    () =>
      dedupeCommands([
        ...commands,
        ...skills.map((skill) => ({
          name: skill.name,
          level: "skill" as const,
          description: skill.description,
          command: skill.command,
          params: ["topic"],
        })),
      ]),
    [commands, skills],
  )

  useEffect(() => {
    function handleGlobalSearchShortcut(event: KeyboardEvent) {
      if (!(event.metaKey || event.ctrlKey)) return
      if (event.key.toLowerCase() !== "k") return
      event.preventDefault()
      setSearchOpen(true)
    }

    window.addEventListener("keydown", handleGlobalSearchShortcut)
    return () => window.removeEventListener("keydown", handleGlobalSearchShortcut)
  }, [])

  const handleNewChat = useCallback((options?: { preserveProject?: boolean }) => {
    activeChatAbortRef.current?.abort()
    activeChatAbortRef.current = null
    activeResearchAbortRef.current?.abort()
    activeResearchAbortRef.current = null
    currentStreamSessionIdRef.current = null
    setSessionId(null)
    setSessionTitle(null)
    setActiveSessionId(null)
    setMessages([])
    setDraft("")
    setBranchContext(null)
    setStatusText(null)
    setActiveTab("chat")
    setShowProjectView(false)
    setShowArtifacts(false)
    if (!options?.preserveProject) setActiveProject(null)
  }, [])

  const handleTabChange = useCallback((tab: ActiveTab) => {
    setActiveTab(tab)
    setShowProjectView(false)
    setShowArtifacts(false)
  }, [])

  const handleOpenArtifacts = useCallback(() => {
    setShowArtifacts(true)
    setShowProjectView(false)
    setActiveTab("chat")
  }, [])

  const handleSelectSession = useCallback(
    (nextSessionId: string) => {
      const selected = sessions.find((session) => session.session_id === nextSessionId)
      const selectedProject = selected?.project_id
        ? projects.find((project) => project.id === selected.project_id) ?? null
        : null
      setSessionId(nextSessionId)
      setSessionTitle(selected?.title || null)
      setActiveProject(selectedProject)
      setShowProjectView(false)
      setShowArtifacts(false)
      setActiveSessionId(nextSessionId)
      setStatusText(null)
      setBranchContext(null)
      setActiveTab("chat")
      void Promise.all([fetchSessionMessages(nextSessionId), fetchSessionTraces(nextSessionId)])
        .then(([fetchedMessages, traces]) => setMessages(attachTracesToMessages(fetchedMessages, traces)))
        .catch(() => setMessages([]))
    },
    [projects, sessions],
  )

  const handleProjectUpdated = useCallback((updated: Project) => {
    setProjectsError(null)
    if (updated.archived) {
      setProjects((current) => current.filter((project) => project.id !== updated.id))
      setActiveProject((current) => (current?.id === updated.id ? null : current))
      setViewingProject((current) => (current?.id === updated.id ? null : current))
      return
    }
    setProjects((current) => {
      const exists = current.some((project) => project.id === updated.id)
      return exists
        ? current.map((project) => (project.id === updated.id ? updated : project))
        : [updated, ...current]
    })
    setActiveProject((current) => (current?.id === updated.id ? updated : current))
    setViewingProject((current) => (current?.id === updated.id ? updated : current))
  }, [])

  const handleSelectProject = useCallback(
    (project: Project) => {
      setViewingProject(project)
      setShowProjectView(true)
      setShowArtifacts(false)
      void fetchProject(project.id)
        .then((updated) => {
          setViewingProject(updated)
          handleProjectUpdated(updated)
        })
        .catch(() => undefined)
    },
    [handleProjectUpdated],
  )

  const handleCreateProject = useCallback(() => {
    setShowNewProjectModal(true)
  }, [])

  const handleAttachProjectToCurrentChat = useCallback(
    async (projectId: string) => {
      let project = projects.find((item) => item.id === projectId) ?? null
      try {
        project = await fetchProject(projectId)
        handleProjectUpdated(project)
      } catch {
        project = project ?? null
      }
      if (!project) return

      setActiveProject(project)
      setShowProjectView(false)
      setShowArtifacts(false)
      setActiveTab("chat")
      if (sessionId) {
        await associateSession(project.id, sessionId)
        await Promise.all([refreshSessions(), refreshProjects()])
      }
    },
    [handleProjectUpdated, projects, refreshProjects, refreshSessions, sessionId],
  )

  const handleProjectCreated = useCallback(
    (project: Project) => {
      handleProjectUpdated(project)
      setActiveProject(project)
      setViewingProject(project)
      handleNewChat({ preserveProject: true })
      setShowNewProjectModal(false)
      setActiveTab("chat")
    },
    [handleNewChat, handleProjectUpdated],
  )

  const handleOpenChat = useCallback(
    async (projectId: string, nextSessionId?: string) => {
      let project = projects.find((item) => item.id === projectId) ?? null
      try {
        project = await fetchProject(projectId)
        handleProjectUpdated(project)
      } catch {
        project = project ?? null
      }
      setShowProjectView(false)
      setShowArtifacts(false)
      setActiveTab("chat")
      if (nextSessionId) {
        handleSelectSession(nextSessionId)
        setActiveProject(project)
      } else {
        setActiveProject(project)
        handleNewChat({ preserveProject: true })
      }
    },
    [handleNewChat, handleProjectUpdated, handleSelectSession, projects],
  )

  const handleRenameSession = useCallback(
    async (title: string) => {
      if (!sessionId) return
      setSessionTitle(title)
      void saveConversationTitle(sessionId, title)
      void refreshSessions()
    },
    [sessionId, refreshSessions],
  )

  const handlePinSession = useCallback(async (sessionIdToPin: string) => {
    try {
      const result = await pinSession(sessionIdToPin)
      setSessions((current) =>
        current
          .map((s) => (s.session_id === sessionIdToPin ? { ...s, pinned: result.pinned } : s))
          .sort((a, b) => {
            const aPinned = !!a.pinned
            const bPinned = !!b.pinned
            if (aPinned && !bPinned) return -1
            if (!aPinned && bPinned) return 1
            return 0
          }),
      )
    } catch {
      // silently ignore
    }
  }, [])

  const handleAddToProject = useCallback((sessionId: string) => {
    setAddToProjectSessionId(sessionId)
  }, [])

  const handleConfirmAddToProject = useCallback(
    async (projectId: string) => {
      if (!addToProjectSessionId) return
      try {
        await addSessionToProject(projectId, addToProjectSessionId)
        await refreshSessions()
      } catch {
        // ignore
      }
      setAddToProjectSessionId(null)
    },
    [addToProjectSessionId, refreshSessions],
  )

  const handleRenameSidebarSession = useCallback(
    async (targetSessionId: string, newTitle: string) => {
      const trimmed = newTitle.trim()
      if (!trimmed) return
      await saveConversationTitle(targetSessionId, trimmed)
      setSessions((current) =>
        current.map((s) => (s.session_id === targetSessionId ? { ...s, title: trimmed } : s)),
      )
      if (targetSessionId === sessionId) {
        setSessionTitle(trimmed)
      }
    },
    [sessionId],
  )

  const handleRememberMessage = useCallback(
    async (message: ChatMessage) => {
      if (ghostMode) return
      if (!message.content.trim()) return
      await addMemory(message.content.slice(0, 2000), "reference")
      setMessages((current) =>
        current.map((item) => (item.id === message.id ? { ...item, remembered: true } : item)),
      )
      window.setTimeout(() => {
        setMessages((current) =>
          current.map((item) => (item.id === message.id ? { ...item, remembered: false } : item)),
        )
      }, 2000)
      void refreshMemory()
    },
    [ghostMode, refreshMemory],
  )

  useEffect(() => {
    if (!memoryWriteNotice) return
    if (memoryWriteNotice.status !== "undone") return
    const timeout = window.setTimeout(() => setMemoryWriteNotice(null), 5000)
    return () => window.clearTimeout(timeout)
  }, [memoryWriteNotice])

  const handleUndoMemoryWrite = useCallback(
    async (eventId: string) => {
      try {
        const result = await undoMemoryWriteEvent(eventId)
        setMemoryWriteNotice(result.event)
        await refreshMemory()
      } catch {
        setStatusText("Memory undo failed")
      }
    },
    [refreshMemory],
  )

  const handleReviewMemoryWrite = useCallback(() => {
    setMemoryOpen(true)
  }, [])

  const handleResearch = useCallback(
    async (query: string) => {
      if (!query || loading) return false

      const assistantId = crypto.randomUUID()
      const startingSessionId = sessionId
      let streamedSessionId: string | null = null
      let researchRunId: string | null = null
      const abortController = new AbortController()

      activeResearchAbortRef.current = abortController
      setLoading(true)
      setStatusText("Starting research...")
      setMessages((current) => {
        const lastMessage = current.at(-1)
        const shouldAppendUser = !(lastMessage?.role === "user" && lastMessage.content.trim() === query.trim())
        return [
          ...current,
          ...(shouldAppendUser
            ? [{ id: crypto.randomUUID(), role: "user" as const, content: query, timestamp: new Date().toISOString() }]
            : []),
          {
          id: assistantId,
          role: "assistant",
          content: "",
          loading: true,
          researchQuery: query,
          researchStatus: "running",
          researchProgress: [],
          timestamp: new Date().toISOString(),
        },
        ]
      })

      try {
        await streamResearch({
          query,
          sessionId,
          projectId: activeProject?.id ?? null,
          ghostMode,
          signal: abortController.signal,
          onStep: ({ label, detail, runId, step, total }) => {
            if (runId) researchRunId = runId
            setStatusText(detail ? `${label}: ${detail}` : label)
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      researchRunId: runId ?? message.researchRunId ?? null,
                      researchStatus: "running",
                      researchProgress: mergeResearchProgress(message.researchProgress, {
                        step,
                        total,
                        label,
                        detail,
                        status: "running",
                      }),
                    }
                  : message,
              ),
            )
          },
          onText: (chunk) => {
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? { ...message, content: message.content + chunk, researchStatus: "running" }
                  : message,
              ),
            )
          },
          onComplete: ({ text, saved, sessionId: nextSessionId, runId, artifactId, sources, qualityScore }) => {
            if (runId) researchRunId = runId
            if (nextSessionId) {
              streamedSessionId = nextSessionId
              setSessionId(nextSessionId)
              setActiveSessionId(nextSessionId)
            }
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      content: text || message.content,
                      loading: false,
                      remembered: saved,
                      researchRunId: runId ?? message.researchRunId ?? null,
                      researchArtifactId: artifactId ?? message.researchArtifactId ?? null,
                      researchSources: sources ?? message.researchSources ?? [],
                      researchQualityScore: qualityScore ?? message.researchQualityScore,
                      researchStatus: "completed",
                      researchProgress: (message.researchProgress ?? []).map((item) => ({
                        ...item,
                        status: "complete",
                      })),
                    }
                  : message,
              ),
            )
          },
          onError: (error) => {
            const friendly = friendlyErrorMessage(error)
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      content: friendly,
                      loading: false,
                      remembered: false,
                      error: friendly,
                      researchStatus: "failed",
                    }
                  : message,
              ),
            )
          },
        })
        if (activeResearchAbortRef.current === abortController) {
          activeResearchAbortRef.current = null
        }
        if (!startingSessionId && streamedSessionId) {
          const titleSessionId = streamedSessionId as string
          void generateConversationTitle(titleSessionId, query).then((title) => {
            if (title) {
              setSessionTitle(title)
              void saveConversationTitle(titleSessionId, title)
              void refreshSessions()
            }
          })
        }
        void Promise.all([refreshMemory(), refreshSessions(), refreshProjects()])
      } catch (error) {
        if (isAbortError(error)) {
          if (researchRunId) {
            void updateResearchRunStatus(researchRunId, "stop").catch(() => undefined)
          }
          setMessages((current) =>
            current.map((item) =>
              item.id === assistantId
                ? {
                    ...item,
                    loading: false,
                    remembered: false,
                    researchRunId: researchRunId ?? item.researchRunId ?? null,
                    researchStatus: "stopped",
                    researchProgress: mergeResearchProgress(item.researchProgress, {
                      step: (item.researchProgress?.length ?? 0) + 1,
                      total: item.researchProgress?.length ?? 0,
                      label: "Research stopped",
                      detail: "Stopped by user",
                      status: "stopped",
                    }),
                  }
                : item,
            ),
          )
          return true
        }
        console.error("Geneva research failed", error)
        const message = friendlyErrorMessage(error)
        setMessages((current) =>
          current.map((item) =>
            item.id === assistantId
              ? {
                  ...item,
                  content: message,
                  loading: false,
                  remembered: false,
                  error: message,
                  researchStatus: "failed",
                }
              : item,
          ),
        )
      } finally {
        if (activeResearchAbortRef.current === abortController) {
          activeResearchAbortRef.current = null
        }
        setLoading(false)
        setStatusText(null)
      }

      return true
    },
    [
      loading,
      refreshMemory,
      refreshProjects,
      refreshSessions,
      sessionId,
      ghostMode,
      activeProject,
    ],
  )

  const sendTurn = useCallback(
    async (rawText: string, attachments: Attachment[] = [], options?: TurnOptions) => {
      const text = rawText.trim()
      if (!text && attachments.length === 0) return false

      if (loading) {
        const trimmed = rawText.trim()
        if (!trimmed) return false
        pendingQueueRef.current = [
          ...pendingQueueRef.current,
          {
            text: trimmed,
            attachments,
            options,
          },
        ]
        setDraft("")
        setStatusText(`ข้อความของคุณจะถูกส่งหลังจาก AI ตอบเสร็จ (${pendingQueueRef.current.length} ข้อความรอ)`)
        return true
      }

      if (researchMode && text) {
        setDraft("")
        setBranchContext(null)
        setResearchMode(false)
        const userMsgId = crypto.randomUUID()
        const planMsgId = crypto.randomUUID()
        setMessages((cur) => [
          ...cur,
          { id: userMsgId, role: "user", content: text },
          { id: planMsgId, role: "assistant", content: "", loading: true },
        ])
        setLoading(true)
        try {
          const plan = await fetchResearchPlan(text, sessionId, null, null)
          setMessages((cur) => cur.map((m) =>
            m.id === planMsgId
              ? { ...m, loading: false, researchPlan: { title: plan.title, steps: plan.steps, query: text } }
              : m
          ))
        } catch {
          // Remove both premature messages, let handleResearch add its own
          setMessages((cur) => cur.filter((m) => m.id !== planMsgId && m.id !== userMsgId))
          return handleResearch(text)
        } finally {
          setLoading(false)
        }
        return true
      }

      const augmentedMessage = buildAugmentedMessage(text, attachments)
      const finalMessage = buildTurnMessage(
        branchContext ? buildBranchedTurnMessage(branchContext, augmentedMessage) : augmentedMessage,
        {
          webSearch: Boolean(options?.webSearch),
        },
      )
      const displayMessage = buildDisplayMessage(text, attachments)
      const hasAttachments = attachments.length > 0
      const startingSessionId = sessionId
      const detectedProject = activeProject ? null : detectProjectFromMessage(text, projects)
      const projectForTurn = activeProject ?? detectedProject
      let streamedSessionId: string | null = null
      let turnAbortController: AbortController | null = null

      setDraft("")
      setBranchContext(null)
      setLoading(true)
      setStatusText("Loading memory context")
      if (detectedProject) setActiveProject(detectedProject)

      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: displayMessage,
        timestamp: new Date().toISOString(),
      }
      setMessages((current) => [...current, userMessage])

      const normalizedCommandText = text.trim()
      const command = !hasAttachments && normalizedCommandText.startsWith("/")
        ? findMatchingCommand(normalizedCommandText, allCommands)
        : null
      const isContextCommand = !hasAttachments && normalizedCommandText === "/context"

      if (command?.level === "client" && command.name === "clear") {
        setMessages([])
        setLoading(false)
        setStatusText(null)
        return true
      }

      if (command?.level === "client" && command.name === "help") {
        const help = allCommands.length
          ? allCommands.map((item) => `${item.command} — ${item.description}`).join("\n")
          : "Try /status, /cost, /memory status, /consult, /engineer, /product-manager, or /gtm-advisor."
        setMessages((current) => [
          ...current,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: help,
            remembered: false,
          },
        ])
        setLoading(false)
        setStatusText(null)
        return true
      }

      const isSkillCommand = command?.level === "skill"
      const skillName = isSkillCommand ? command?.name : undefined
      const selectedSkill = isSkillCommand ? skills.find((skill) => skill.name === skillName) : undefined
      const skillInvocationScope = isSkillCommand ? options?.skillScope ?? "once" : undefined

      const assistantId = crypto.randomUUID()
      if (command?.name === "context" || isContextCommand) {
        setMemoryOpen(true)
        setStatusText("Opening Context Inspector")
      }
      const assistantStartTime = new Date().toISOString()
      setMessages((current) => [
        ...current,
        {
          id: assistantId,
          role: "assistant",
          content: "",
          loading: true,
          skillName,
          skillDescription: selectedSkill?.description,
          skillSafetyStatus: selectedSkill?.safety_status ?? null,
          skillInvocationScope,
          timestamp: assistantStartTime,
        },
      ])

      try {
        if (command?.level === "server" || isContextCommand) {
          const result = await executeCommand({
            raw: normalizedCommandText,
            sessionId,
          })
          if (result.sessionId) {
            setSessionId(result.sessionId)
            setActiveSessionId(result.sessionId)
          }
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantId
                ? {
                    ...message,
                    content:
                      command?.name === "context" || isContextCommand
                        ? formatContextCommandOutput(result.text)
                        : result.text || "Command completed.",
                    loading: false,
                    remembered: false,
                  }
                : message,
            ),
          )
        } else {
          const abortController = new AbortController()
          turnAbortController = abortController
          activeChatAbortRef.current = abortController
          currentStreamSessionIdRef.current = sessionId
          await streamChat({
            message: finalMessage,
            sessionId,
            projectId: projectForTurn?.id,
            ghostMode,
            modeId: options?.modeId,
            images: attachmentsToImages(attachments),
            signal: abortController.signal,
            onText: (chunk) => {
              setMessages((current) =>
                current.map((message) =>
                  message.id === assistantId ? { ...message, content: message.content + chunk } : message,
                ),
              )
            },
            onEvent: (event) => {
              const nextStatusText = statusTextForStreamEvent(event)
              if (nextStatusText) setStatusText(nextStatusText)
              const activityEvent = activityFromStreamEvent(event, assistantId)
              if (activityEvent) {
                setMessages((current) =>
                  current.map((message) =>
                    message.id === assistantId
                      ? {
                          ...message,
                          activityEvents: mergeActivityEvent(message.activityEvents, activityEvent),
                          error:
                            activityEvent.status === "error" || activityEvent.status === "timeout"
                              ? activityEvent.error ?? activityEvent.detail ?? message.error
                              : message.error,
                        }
                      : message,
                  ),
                )
              }
              if (event.type === "memory_update") {
                const writeEvent = memoryWriteEventFromPayload(event.data?.write_event)
                if (writeEvent) setMemoryWriteNotice(writeEvent)
              }
              if (event.type === "turn_complete") {
                const contextSummary = contextSummaryFromPayload(event.data?.context_summary)
                if (contextSummary) {
                  setMessages((current) =>
                    current.map((message) =>
                      message.id === assistantId ? { ...message, contextSummary } : message,
                    ),
                  )
                }
                setMessages((current) =>
                  current.map((message) =>
                    message.id === assistantId ? { ...message, loading: false, remembered: false } : message,
                  ),
                )
                setLoading(false)
                setStatusText(null)
              }

              if (event.type === "tool_permission_request") {
                const requestId = String(event.data?.request_id ?? "")
                const permissionSessionId = String(event.data?.session_id ?? sessionId ?? "")
                if (requestId && permissionSessionId) {
                  setPermissionRequest({
                    requestId,
                    sessionId: permissionSessionId,
                    toolName: String(event.data?.tool_name ?? "Tool"),
                    message: String(event.data?.message ?? "This tool needs permission before it can run."),
                    suggestion:
                      typeof event.data?.suggestion === "string"
                        ? event.data.suggestion
                        : null,
                    timeoutSeconds:
                      typeof event.data?.timeout_seconds === "number"
                        ? event.data.timeout_seconds
                        : 60,
                  })
                }
              }
              if (event.type === "tool_permission_resolved") {
                const requestId = String(event.data?.request_id ?? "")
                setPermissionRequest((current) => (current?.requestId === requestId ? null : current))
              }

              const toolTrace = traceFromStreamEvent(event)
              if (toolTrace) {
                setMessages((current) =>
                  current.map((message) =>
                    message.id === assistantId
                      ? {
                          ...message,
                          toolEvents: mergeToolTrace(message.toolEvents, toolTrace),
                        }
                      : message,
                  ),
                )
              }
            },
            onSession: (nextSessionId) => {
              streamedSessionId = nextSessionId
              currentStreamSessionIdRef.current = nextSessionId
              setSessionId(nextSessionId)
              setActiveSessionId(nextSessionId)
              if (projectForTurn) {
                void associateSession(projectForTurn.id, nextSessionId)
              }
            },
          })
          if (activeChatAbortRef.current === abortController) {
            activeChatAbortRef.current = null
          }
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantId ? { ...message, loading: false, remembered: false } : message,
            ),
          )
          // Auto-send queued message if any
          if (pendingQueueRef.current.length > 0) {
            const next = pendingQueueRef.current.shift()!
            void sendTurn(next.text, next.attachments, next.options)
          }
          if (!startingSessionId && streamedSessionId) {
            const titleSessionId = streamedSessionId as string
            void generateConversationTitle(titleSessionId, text).then((title) => {
              if (title) {
                setSessionTitle(title)
                void saveConversationTitle(titleSessionId, title)
                void refreshSessions()
              }
            })
          }
        }
        void Promise.all([refreshMemory(), refreshSessions(), refreshProjects()])
      } catch (error) {
        if (isAbortError(error)) {
          setMessages((current) =>
            current.map((item) =>
              item.id === assistantId
                ? {
                    ...item,
                    loading: false,
                    remembered: false,
                  }
                : item,
            ),
          )
          return true
        }
        console.error("Geneva chat failed", error)
        const message = friendlyErrorMessage(error)
        setMessages((current) =>
          current.map((item) =>
            item.id === assistantId
              ? {
                  ...item,
                  content: message,
                  loading: false,
                  remembered: false,
                  error: message,
                }
              : item,
          ),
        )
      } finally {
        if (turnAbortController && activeChatAbortRef.current === turnAbortController) {
          activeChatAbortRef.current = null
        }
        setLoading(false)
        setStatusText(null)
      }

      return true
    },
    [
      allCommands,
      branchContext,
      loading,
      refreshMemory,
      refreshProjects,
      refreshSessions,
      sessionId,
      activeProject,
      ghostMode,
      handleResearch,
      projects,
      researchMode,
      skills,
    ],
  )

  const handleSend = useCallback(
    async (attachments: Attachment[] = [], options?: TurnOptions) => sendTurn(draft, attachments, options),
    [draft, sendTurn],
  )

  const handleAmend = useCallback(
    async (message: string) => {
      const text = message.trim()
      if (!text || !sessionId || !isStreaming) return false

      try {
        await amendConversation(sessionId, text)
        setDraft("")
        setStatusText("Interrupt sent")
        return true
      } catch (error) {
        console.error("Geneva amend failed", error)
        setStatusText(friendlyErrorMessage(error))
        return false
      }
    },
    [isStreaming, sessionId],
  )

  // Auto-send pending message (e.g. from Create with Geneva)
  useEffect(() => {
    if (!pendingAutoSendRef.current || loading) return
    const msg = pendingAutoSendRef.current
    pendingAutoSendRef.current = null
    const timer = window.setTimeout(() => { void sendTurn(msg) }, 120)
    return () => window.clearTimeout(timer)
  }, [activeTab, loading, sendTurn])

  const handleStop = useCallback(async () => {
    const stopSessionId = currentStreamSessionIdRef.current ?? sessionId
    const stopResearchRunId = messages.find((msg) => msg.role === "assistant" && msg.loading && msg.researchRunId)?.researchRunId ?? null
    activeChatAbortRef.current?.abort()
    activeChatAbortRef.current = null
    activeResearchAbortRef.current?.abort()
    activeResearchAbortRef.current = null
    pendingQueueRef.current = []
    // Optimistic: immediately update UI
    setLoading(false)
    setStatusText(null)
    setMessages((current) =>
      current.map((msg) =>
        msg.role === "assistant" && msg.loading
          ? {
              ...msg,
              loading: false,
              researchStatus: msg.researchQuery ? "stopped" : msg.researchStatus,
            }
          : msg,
      ),
    )
    if (stopResearchRunId) {
      void updateResearchRunStatus(stopResearchRunId, "stop").catch(() => undefined)
    }
    if (!stopSessionId) return
    // Signal backend to cancel
    try {
      await fetch(`/api/sessions/${encodeURIComponent(stopSessionId)}/stop`, {
        method: "POST",
        headers: { [TRUSTED_REQUEST_HEADER]: "1" },
      })
    } catch {
      setStatusText("หยุดไม่ได้ กรุณาลองใหม่")
    }
  }, [messages, sessionId])

  const handleDeleteSession = useCallback(async (sessionToDelete: string) => {
    try {
      const res = await fetch(`/api/sessions/${sessionToDelete}`, {
        method: "DELETE",
        headers: { [TRUSTED_REQUEST_HEADER]: "1" },
      })
      if (!res.ok) return
      // If deleting the active session, start a new chat
      if (sessionToDelete === sessionId) {
        handleNewChat()
      }
      // Refresh session list
      void refreshSessions()
    } catch {
      // silently ignore
    }
  }, [sessionId, handleNewChat, refreshSessions])

  const handleEditMessage = useCallback(
    (messageId: string) => {
      const message = messages.find((item) => item.id === messageId)
      if (!message || message.role !== "user") return
      setDraft(cleanMessageForDraft(message.content))
    },
    [messages],
  )

  const handleSaveEdit = useCallback(
    async (serverId: string | undefined, frontendId: string, newText: string) => {
      if (loading || !sessionId) return
      setMessages((current) => {
        const idx = current.findIndex((m) => m.id === frontendId)
        if (idx === -1) return current
        return current.slice(0, idx)
      })
      if (serverId) {
        try {
          await fetch(`/api/sessions/${sessionId}/edit`, {
            method: "POST",
            headers: { [TRUSTED_REQUEST_HEADER]: "1", "Content-Type": "application/json" },
            body: JSON.stringify({ message_id: serverId, new_text: newText }),
          })
        } catch {
          // backend sync failed — proceed anyway
        }
      }
      void sendTurn(newText)
    },
    [loading, sessionId, sendTurn, setMessages],
  )

  const handleRetryMessage = useCallback(
    async () => {
      if (loading || !sessionId) return
      try {
        const res = await fetch(`/api/sessions/${sessionId}/retry`, {
          method: "POST",
          headers: { [TRUSTED_REQUEST_HEADER]: "1", "Content-Type": "application/json" },
          body: JSON.stringify({}),
        })
        if (!res.ok) return
        const data = (await res.json()) as { retry_text?: string }
        const retryText = data.retry_text
        if (!retryText) return
        // Remove last assistant + its preceding user message from UI (backend also removed both)
        setMessages((current) => {
          const lastAssistantIdx = [...current].reverse().findIndex((m) => m.role === "assistant")
          if (lastAssistantIdx === -1) return current
          const actualAssistantIdx = current.length - 1 - lastAssistantIdx
          // Find the user message before it
          let cutAt = actualAssistantIdx
          for (let i = actualAssistantIdx - 1; i >= 0; i--) {
            if (current[i].role === "user") { cutAt = i; break }
          }
          return current.slice(0, cutAt)
        })
        void sendTurn(retryText)
      } catch {
        // silently ignore
      }
    },
    [loading, sessionId, sendTurn, setMessages],
  )

  const handleForkMessage = useCallback(
    (messageId: string) => {
      const index = messages.findIndex((message) => message.id === messageId)
      if (index < 0) return
      const branchMessages = messages.slice(0, index + 1).map((message) => ({
        ...message,
        loading: false,
      }))
      setSessionId(null)
      setSessionTitle("Branched chat")
      setActiveSessionId(null)
      setMessages(branchMessages)
      setBranchContext(buildBranchTranscript(branchMessages))
      setDraft("")
      setStatusText(null)
      setActiveTab("chat")
      setShowProjectView(false)
      setShowArtifacts(false)
    },
    [messages],
  )

  const composer = (
    <Composer
      commands={allCommands}
      isStreaming={isStreaming}
      loading={loading}
      modeId={composerModeId}
      onAmend={handleAmend}
      onModeChange={setComposerModeId}
      onSend={handleSend}
      onToggleResearch={() => setResearchMode((enabled) => !enabled)}
      activeProjectId={activeProject?.id ?? null}
      onCreateProject={handleCreateProject}
      onSelectProject={handleAttachProjectToCurrentChat}
      onValueChange={setDraft}
      onStop={handleStop}
      projects={projects}
      researchMode={researchMode}
      value={draft}
    />
  )

  const handleQuickSwitch = useCallback((trigger: string) => {
    setDraft(trigger)
    setActiveTab("chat")
  }, [])

  const handleCreateSkillChat = useCallback(() => {
    setMessages([])
    setSessionId(null)
    setSessionTitle(null)
    setActiveTab("chat")
    setShowArtifacts(false)
    setDraft("/skill_builder ")
  }, [])

  const handleResolvePermission = useCallback(
    async (request: ToolPermissionRequest, approved: boolean) => {
      setPermissionRequest(null)
      setStatusText(approved ? "Tool approved" : "Tool denied")
      try {
        await resolveToolPermission(request.sessionId, request.requestId, approved)
      } catch (error) {
        console.error("Failed to resolve tool permission", error)
        setStatusText("Permission response failed")
      }
    },
    [],
  )

  return (
    <>
      <AppShell
        memoryOpen={memoryOpen}
        memoryPanel={
          <Suspense fallback={null}>
            <MemoryPanel
              activeProject={activeProject}
              onClose={() => setMemoryOpen(false)}
              sessionId={sessionId}
              stats={memoryStats}
            />
          </Suspense>
        }
        sidebarCollapsed={activeTab === "skill" || effectiveSidebarCollapsed}
        skillMode={activeTab === "skill"}
        sidebar={
          <Sidebar
            activeSessionId={sessionId}
            activeProjectId={activeProject?.id ?? null}
            activeTab={activeTab}
            collapsed={effectiveSidebarCollapsed}
            memoryStats={memoryStats}
            onNewChat={handleNewChat}
            onCreateProject={handleCreateProject}
            onOpenArtifacts={handleOpenArtifacts}
            onOpenSource={() => setShowOpenSource(true)}
            onOpenSearch={() => setSearchOpen(true)}
            onOpenSettings={() => setShowSettings(true)}
            onOpenProjectChat={(project) => void handleOpenChat(project.id)}
            onSelectProject={handleSelectProject}
            onSelectSession={handleSelectSession}
            onDeleteSession={handleDeleteSession}
            onPinSession={handlePinSession}
            onAddToProject={handleAddToProject}
            onRenameSession={handleRenameSidebarSession}
            onTabChange={handleTabChange}
            onToggleCollapsed={() => setSidebarCollapsed((collapsed) => !collapsed)}
            onRetryProjects={() => void refreshProjects()}
            projects={projects}
            projectsError={projectsError}
            projectsLoading={projectsLoading}
            sessions={sessions}
          />
        }
      >
        {showArtifacts ? (
          <Suspense fallback={<ViewLoading label="Opening artifacts" />}>
            <ArtifactsSurface
              activeProject={activeProject}
              onBack={() => setShowArtifacts(false)}
              projects={projects}
              sessionId={sessionId}
            />
          </Suspense>
        ) : null}
        {!showArtifacts && showProjectView && viewingProject ? (
          <Suspense fallback={<ViewLoading label="Opening project" />}>
            <ProjectView
              onClose={() => setShowProjectView(false)}
              onOpenChat={handleOpenChat}
              onUpdate={handleProjectUpdated}
              project={viewingProject}
            />
          </Suspense>
        ) : null}
        {!showArtifacts && !showProjectView && activeTab === "chat" ? (
          <ChatCanvas
            activeProject={activeProject}
            composer={composer}
            ghostMode={ghostMode}
            loading={loading}
            memoryStats={memoryStats}
            memoryWriteNotice={memoryWriteNotice}
            messages={messages}
            onClearProject={() => setActiveProject(null)}
            onEditMessage={handleEditMessage}
            onSaveEdit={handleSaveEdit}
            onForkMessage={handleForkMessage}
            onRememberMessage={handleRememberMessage}
            onReviewMemoryWrite={handleReviewMemoryWrite}
            onRenameSession={sessionId ? handleRenameSession : undefined}
            onRetryMessage={handleRetryMessage}
            onUndoMemoryWrite={handleUndoMemoryWrite}
            onDismissMemoryWrite={() => setMemoryWriteNotice(null)}
            onToggleGhost={() => setGhostMode((enabled) => !enabled)}
            onQuickAction={(text) => setDraft(text)}
            onOpenArtifacts={handleOpenArtifacts}
            onStartResearch={(query) => { void handleResearch(query) }}
            onCancelResearchPlan={(id) => setMessages((cur) => cur.filter((m) => m.id !== id))}
            sessionTitle={sessionTitle}
            statusText={statusText}
          />
        ) : null}
        {!showArtifacts && !showProjectView && activeTab === "skill" ? (
          <CustomizeSurface
            currentSessionId={sessionId}
            onBack={() => handleTabChange("chat")}
            onCreateSkillChat={handleCreateSkillChat}
            onSelectSkill={handleQuickSwitch}
            onSkillsChanged={setSkills}
            pendingPermissionRequest={permissionRequest}
            skills={skills}
          />
        ) : null}
      </AppShell>
      {showSettings ? (
        <Suspense fallback={<ViewLoading label="Opening settings" />}>
          <Settings
            currentModeId={composerModeId}
            effectiveDarkMode={effectiveDarkMode}
            onClose={() => {
              setShowSettings(false)
              void refreshSkills()
            }}
            onDefaultModeChange={setComposerModeId}
            onThemeModeChange={handleThemeModeChange}
            themeMode={themeMode}
          />
        </Suspense>
      ) : null}
      <SearchOverlay
        activeProjectId={(showProjectView ? viewingProject?.id : activeProject?.id) ?? null}
        activeSessionId={sessionId}
        onClose={() => setSearchOpen(false)}
        onOpenMemory={() => setMemoryOpen(true)}
        onSelectProject={handleSelectProject}
        onSelectSession={handleSelectSession}
        open={searchOpen}
        projects={projects}
        sessions={sessions}
      />
      {showOpenSource ? <OpenSourceModal onClose={() => setShowOpenSource(false)} /> : null}
      {addToProjectSessionId && projects.length > 0 ? (
        <div className="project-picker-overlay" onClick={() => setAddToProjectSessionId(null)}>
          <div className="project-picker-panel" onClick={(event) => event.stopPropagation()}>
            <p className="project-picker-title">Add to project</p>
            {projects.map((project) => (
              <button
                className="project-picker-item"
                key={project.id}
                onClick={() => handleConfirmAddToProject(project.id)}
                type="button"
              >
                <span className="project-dot" style={{ background: project.color }} />
                <span>{project.name}</span>
              </button>
            ))}
            <button
              className="project-picker-cancel"
              onClick={() => setAddToProjectSessionId(null)}
              type="button"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : null}
      {permissionRequest ? (
        <ToolPermissionModal
          onResolve={(approved) => void handleResolvePermission(permissionRequest, approved)}
          request={permissionRequest}
        />
      ) : null}
      {showNewProjectModal ? (
        <Suspense fallback={null}>
          <NewProjectModal
            onClose={() => setShowNewProjectModal(false)}
            onCreated={handleProjectCreated}
          />
        </Suspense>
      ) : null}
    </>
  )
}

export default App
