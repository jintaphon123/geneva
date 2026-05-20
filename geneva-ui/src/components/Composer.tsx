import {
  type ChangeEvent,
  type KeyboardEvent,
  type ReactNode,
  useEffect,
  useRef,
  useState,
} from "react"
import {
  ArrowUp,
  ChevronRight,
  FileText,
  FolderPlus,
  Globe2,
  MessageSquarePlus,
  Mic,
  Paperclip,
  Plus,
  Search,
  Square,
  Sparkles,
  Telescope,
  UploadCloud,
  X,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { Attachment, Project, SkillInvocationScope, SlashCommand } from "@/types"

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike
type SpeechRecognitionLike = {
  continuous: boolean
  interimResults: boolean
  lang: string
  onend: (() => void) | null
  onerror: ((event: { error?: string }) => void) | null
  onresult: ((event: SpeechRecognitionResultEventLike) => void) | null
  start: () => void
  stop: () => void
}
type SpeechRecognitionResultEventLike = {
  results: ArrayLike<ArrayLike<{ transcript: string }>>
}

type ComposerModeId = "low" | "medium" | "high" | "extra_high"

const COMPOSER_MODES: Array<{
  id: ComposerModeId
  label: string
  description: string
}> = [
  { id: "low", label: "Low", description: "Fast, light reasoning" },
  { id: "medium", label: "Medium", description: "Balanced default" },
  { id: "high", label: "High", description: "More careful work" },
  { id: "extra_high", label: "Extra High", description: "Deepest pass" },
]

type SlashCommandGroup = "System" | "Project" | "Memory" | "Research" | "Developer" | "Skills"

const SLASH_COMMAND_GROUPS: SlashCommandGroup[] = [
  "System",
  "Project",
  "Memory",
  "Research",
  "Developer",
  "Skills",
]

const SLASH_LEVEL_LABEL: Record<SlashCommand["level"], string> = {
  client: "System",
  server: "System",
  skill: "Skill",
}

const SLASH_GROUP_TERMS: Record<Exclude<SlashCommandGroup, "System" | "Skills">, string[]> = {
  Project: ["project", "todo", "task", "source", "artifact", "workspace"],
  Memory: ["memory", "remember", "context", "recall", "preference"],
  Research: ["research", "deep", "search", "web", "report", "investigate"],
  Developer: ["code", "debug", "review", "test", "shell", "terminal", "engineer", "github", "codex"],
}

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor
    webkitSpeechRecognition?: SpeechRecognitionConstructor
  }
}

type ComposerProps = {
  value: string
  onValueChange: (value: string) => void
  onSend: (
    attachments: Attachment[],
    options?: { webSearch?: boolean; modeId?: string; skillScope?: SkillInvocationScope },
  ) => Promise<boolean> | boolean | void
  onAmend: (message: string) => Promise<boolean> | boolean | void
  loading: boolean
  isStreaming: boolean
  commands: SlashCommand[]
  modeId?: ComposerModeId
  onModeChange?: (modeId: ComposerModeId) => void
  researchMode: boolean
  onToggleResearch: () => void
  projects?: Project[]
  activeProjectId?: string | null
  onSelectProject?: (projectId: string) => Promise<void> | void
  onCreateProject?: () => void
  onStop?: () => void
}

export function Composer({
  value,
  onValueChange,
  onSend,
  onAmend,
  loading,
  isStreaming,
  commands,
  modeId = "medium",
  onModeChange,
  researchMode,
  onToggleResearch,
  projects = [],
  activeProjectId,
  onSelectProject,
  onCreateProject,
  onStop,
}: ComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const attachMenuRef = useRef<HTMLDivElement | null>(null)
  const modeMenuRef = useRef<HTMLDivElement | null>(null)
  const speechRef = useRef<SpeechRecognitionLike | null>(null)
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const [dragActive, setDragActive] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [modeMenuOpen, setModeMenuOpen] = useState(false)
  const [openSubmenu, setOpenSubmenu] = useState<"project" | "skill" | null>(null)
  const [webSearchMode, setWebSearchMode] = useState(false)
  const [skillSearch, setSkillSearch] = useState("")
  const [skillScope, setSkillScope] = useState<SkillInvocationScope>("once")
  const [popupIndex, setPopupIndex] = useState(0)
  const [listening, setListening] = useState(false)
  const [voiceError, setVoiceError] = useState<string | null>(null)

  const slashMatch = /^\/([\w-]*)$/.exec(value)
  const slashQuery = slashMatch ? slashMatch[1].toLowerCase() : null
  const showPopup = slashQuery !== null && commands.length > 0
  const filtered = showPopup
    ? commands.filter((command) => matchesSlashCommand(command, slashQuery)).slice(0, 14)
    : []
  const slashSections = SLASH_COMMAND_GROUPS.map((label) => ({
    label,
    commands: filtered.filter((command) => slashCommandGroup(command) === label),
  })).filter((section) => section.commands.length > 0)
  const skillCommands = commands.filter((command) => command.level === "skill")
  const filteredSkillCommands = skillCommands
    .filter((command) => {
      const needle = skillSearch.trim().toLowerCase()
      if (!needle) return true
      return (
        command.name.toLowerCase().includes(needle) ||
        command.command.toLowerCase().includes(needle) ||
        command.description.toLowerCase().includes(needle)
      )
    })
    .slice(0, 10)
  const visibleProjects = projects.filter((project) => !project.archived)
  const availableProjects = visibleProjects.slice(0, 8)
  const activeProject = activeProjectId
    ? visibleProjects.find((project) => project.id === activeProjectId) ?? null
    : null
  const voiceSupported =
    typeof window !== "undefined" &&
    Boolean(window.SpeechRecognition ?? window.webkitSpeechRecognition)
  const hasDraft = value.trim().length > 0
  const hasPayload = hasDraft || attachments.length > 0
  const canSend = isStreaming ? hasDraft : hasPayload
  const selectedMode = COMPOSER_MODES.find((mode) => mode.id === modeId) ?? COMPOSER_MODES[1]
  const activeComposerPills: Array<{ id: string; label: string; element: ReactNode }> = []
  if (activeProject) {
    activeComposerPills.push({
      id: "project",
      label: `Project: ${activeProject.name}`,
      element: (
        <span className="composer-context-pill ui8-overflow-safe">
          <span className="project-dot" style={{ background: activeProject.color }} />
          Project: {activeProject.name}
        </span>
      ),
    })
  }
  if (researchMode) {
    activeComposerPills.push({
      id: "research",
      label: "Deep Research on",
      element: (
        <button
          aria-pressed="true"
          className="composer-mode-pill ui8-overflow-safe"
          onClick={onToggleResearch}
          type="button"
        >
          <Telescope className="size-3.5" />
          Deep Research on
        </button>
      ),
    })
  }
  if (webSearchMode) {
    activeComposerPills.push({
      id: "web-search",
      label: "Web Search on",
      element: (
        <button
          aria-pressed="true"
          className="composer-mode-pill web-search ui8-overflow-safe"
          onClick={() => setWebSearchMode(false)}
          type="button"
        >
          <Globe2 className="size-3.5" />
          Web Search on
        </button>
      ),
    })
  }
  const visibleComposerPills = activeComposerPills.slice(0, 2)
  const hiddenComposerPillCount = Math.max(0, activeComposerPills.length - visibleComposerPills.length)
  const hiddenComposerPillLabels = activeComposerPills
    .slice(visibleComposerPills.length)
    .map((pill) => pill.label)
    .join(", ")

  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = "0px"
    const lineHeight = 21
    const maxHeight = lineHeight * 7 + 18
    textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`
  }, [value])

  useEffect(() => {
    setPopupIndex(0)
  }, [value])

  useEffect(() => {
    if (popupIndex < filtered.length) return
    setPopupIndex(0)
  }, [filtered.length, popupIndex])

  useEffect(() => {
    if (!menuOpen && !modeMenuOpen) return

    function handlePointerDown(event: MouseEvent) {
      const target = event.target
      if (!(target instanceof Node)) return
      if (menuOpen && !attachMenuRef.current?.contains(target)) {
        setMenuOpen(false)
        setOpenSubmenu(null)
      }
      if (modeMenuOpen && !modeMenuRef.current?.contains(target)) {
        setModeMenuOpen(false)
      }
    }

    document.addEventListener("mousedown", handlePointerDown)
    return () => document.removeEventListener("mousedown", handlePointerDown)
  }, [menuOpen, modeMenuOpen])

  useEffect(() => {
    if (!menuOpen) setSkillSearch("")
  }, [menuOpen])

  useEffect(() => {
    function handleWindowDragEnter(event: globalThis.DragEvent) {
      if (!isFileDrag(event)) return
      event.preventDefault()
      if (!loading) setDragActive(true)
    }

    function handleWindowDragOver(event: globalThis.DragEvent) {
      if (!isFileDrag(event)) return
      event.preventDefault()
      if (event.dataTransfer) event.dataTransfer.dropEffect = "copy"
      if (!loading) setDragActive(true)
    }

    function handleWindowDragLeave(event: globalThis.DragEvent) {
      if (event.clientX <= 0 || event.clientY <= 0) {
        setDragActive(false)
        return
      }
      if (event.clientX >= window.innerWidth || event.clientY >= window.innerHeight) {
        setDragActive(false)
      }
    }

    function handleWindowDrop(event: globalThis.DragEvent) {
      if (!isFileDrag(event)) return
      event.preventDefault()
      setDragActive(false)
      if (loading) return
      addFiles(Array.from(event.dataTransfer?.files ?? []))
    }

    window.addEventListener("dragenter", handleWindowDragEnter)
    window.addEventListener("dragover", handleWindowDragOver)
    window.addEventListener("dragleave", handleWindowDragLeave)
    window.addEventListener("drop", handleWindowDrop)
    return () => {
      window.removeEventListener("dragenter", handleWindowDragEnter)
      window.removeEventListener("dragover", handleWindowDragOver)
      window.removeEventListener("dragleave", handleWindowDragLeave)
      window.removeEventListener("drop", handleWindowDrop)
    }
  }, [loading])

  useEffect(
    () => () => {
      speechRef.current?.stop()
    },
    [],
  )

  function handleSubmit() {
    if (!canSend) return
    if (listening) {
      speechRef.current?.stop()
      setListening(false)
    }
    if (isStreaming) {
      const text = value.trim()
      const result = onAmend(text)
      void Promise.resolve(result).then((sent) => {
        if (sent !== false) {
          onValueChange("")
        }
      })
      return
    }
    const result = onSend(attachments, { webSearch: webSearchMode, modeId: selectedMode.id, skillScope })
    void Promise.resolve(result).then((sent) => {
      if (sent !== false) {
        setAttachments([])
        setWebSearchMode(false)
      }
    })
  }

  function closeAttachMenu() {
    setMenuOpen(false)
    setOpenSubmenu(null)
  }

  function handleAttachFile() {
    closeAttachMenu()
    fileInputRef.current?.click()
  }

  function handleSelectProject(projectId: string) {
    closeAttachMenu()
    void onSelectProject?.(projectId)
  }

  function handleCreateProject() {
    closeAttachMenu()
    onCreateProject?.()
  }

  function handleDeepResearch() {
    closeAttachMenu()
    onToggleResearch()
  }

  function handleWebSearch() {
    closeAttachMenu()
    setWebSearchMode((enabled) => !enabled)
  }

  function handleUseSkill(command: SlashCommand) {
    closeAttachMenu()
    onValueChange(`/${command.name} `)
  }

  function handleVoiceInput() {
    if (loading) return
    if (listening) {
      speechRef.current?.stop()
      setListening(false)
      return
    }
    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition
    if (!Recognition) {
      setVoiceError("Voice input is not available in this browser.")
      window.setTimeout(() => setVoiceError(null), 3200)
      return
    }
    const recognition = new Recognition()
    speechRef.current = recognition
    recognition.lang = "th-TH"
    recognition.continuous = false
    recognition.interimResults = false
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0]?.transcript ?? "")
        .join(" ")
        .trim()
      if (transcript) {
        onValueChange(value ? `${value.trimEnd()} ${transcript}` : transcript)
      }
    }
    recognition.onerror = () => {
      setVoiceError("Could not capture voice input. Type the message instead.")
      window.setTimeout(() => setVoiceError(null), 3200)
    }
    recognition.onend = () => setListening(false)
    setVoiceError(null)
    setListening(true)
    try {
      recognition.start()
    } catch {
      setListening(false)
      setVoiceError("Voice input could not start. Type the message instead.")
      window.setTimeout(() => setVoiceError(null), 3200)
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (showPopup && filtered.length > 0) {
      if (event.key === "ArrowDown") {
        event.preventDefault()
        setPopupIndex((index) => (index + 1) % filtered.length)
        return
      }
      if (event.key === "ArrowUp") {
        event.preventDefault()
        setPopupIndex((index) => (index - 1 + filtered.length) % filtered.length)
        return
      }
      if (event.key === "Tab" || event.key === "Enter") {
        event.preventDefault()
        const selected = filtered[popupIndex] ?? filtered[0]
        onValueChange(`/${selected.name} `)
        setPopupIndex(0)
        return
      }
      if (event.key === "Escape") {
        event.preventDefault()
        onValueChange("")
        return
      }
    }

    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      handleSubmit()
    }
  }

  function addFiles(files: File[]) {
    for (const file of files) {
      const id = `${file.name}-${file.lastModified}-${file.size}-${crypto.randomUUID()}`
      if (file.type.startsWith("image/")) {
        const reader = new FileReader()
        reader.onload = () => {
          setAttachments((current) => [
            ...current,
            {
              id,
              name: file.name,
              type: "image",
              dataUrl: typeof reader.result === "string" ? reader.result : undefined,
              size: file.size,
            },
          ])
        }
        reader.readAsDataURL(file)
      } else if (/\.(txt|md|csv|json|py|ts|tsx|js|yaml|yml)$/i.test(file.name)) {
        const reader = new FileReader()
        reader.onload = () => {
          setAttachments((current) => [
            ...current,
            {
              id,
              name: file.name,
              type: "text",
              text: typeof reader.result === "string" ? reader.result : "",
              size: file.size,
            },
          ])
        }
        reader.readAsText(file)
      } else {
        setAttachments((current) => [
          ...current,
          {
            id,
            name: file.name,
            type: "unknown",
            size: file.size,
          },
        ])
      }
    }
  }

  function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    addFiles(Array.from(event.target.files ?? []))
    event.target.value = ""
  }

  return (
    <div className={cn("composer-shell", dragActive && "dragging", loading && "is-loading")}>
      <input
        accept="image/*,.txt,.md,.csv,.json,.py,.ts,.tsx,.js,.yaml,.yml"
        hidden
        multiple
        onChange={handleFiles}
        ref={fileInputRef}
        type="file"
      />
      {showPopup && filtered.length > 0 ? (
        <div aria-label="Slash commands" className="slash-popup" role="listbox">
          <div className="slash-popup-hint">Type to filter</div>
          {slashSections.map((section) => (
            <div className="slash-popup-section" key={section.label}>
              <div className="slash-popup-section-title">{section.label}</div>
              {section.commands.map((command) => {
                const index = filtered.findIndex((item) => item.command === command.command)
                return (
                  <button
                    aria-selected={index === popupIndex}
                    className={cn("slash-popup-row", index === popupIndex && "highlighted")}
                    key={command.command}
                    onMouseDown={(event) => {
                      event.preventDefault()
                      onValueChange(`/${command.name} `)
                      setPopupIndex(0)
                    }}
                    onMouseEnter={() => setPopupIndex(index)}
                    role="option"
                    type="button"
                  >
                    <span className={cn("slash-popup-icon", `is-${slashCommandGroup(command).toLowerCase()}`)}>
                      {slashCommandIcon(command)}
                    </span>
                    <span className="slash-popup-copy">
                      <span className={cn("slash-popup-cmd", `is-${command.level}`)}>/{command.name}</span>
                      <span className="slash-popup-desc">{command.description}</span>
                    </span>
                    <span className={cn("slash-popup-level", `is-${command.level}`)}>
                      {slashCommandGroup(command) === "Skills"
                        ? SLASH_LEVEL_LABEL[command.level]
                        : slashCommandGroup(command)}
                    </span>
                  </button>
                )
              })}
            </div>
          ))}
        </div>
      ) : null}
      {dragActive ? (
        <div className="global-drop-overlay">
          <div className="global-drop-card">
            <UploadCloud className="size-12" />
            <p>Drop files here to add to chat</p>
          </div>
        </div>
      ) : null}
      <div
        className={cn(
          "composer-box",
          researchMode && "research-mode",
          hasPayload && "has-payload",
          attachments.length > 0 && "has-attachments",
          listening && "is-listening",
        )}
      >
        {attachments.length > 0 ? (
          <div className="attachment-tray">
            {attachments.map((attachment) => (
              <div className="attachment-chip" key={attachment.id}>
                {attachment.type === "image" && attachment.dataUrl ? (
                  <img alt={attachment.name} className="att-thumb" src={attachment.dataUrl} />
                ) : (
                  <FileText className="size-3.5 shrink-0" />
                )}
                <span className="att-name">
                  {attachment.name.length > 22 ? `${attachment.name.slice(0, 19)}...` : attachment.name}
                </span>
                <button
                  aria-label={`Remove ${attachment.name}`}
                  className="att-remove"
                  onClick={() =>
                    setAttachments((current) => current.filter((item) => item.id !== attachment.id))
                  }
                  type="button"
                >
                  <X className="size-3" />
                </button>
              </div>
            ))}
          </div>
        ) : null}
        <textarea
          aria-label="Message"
          className="composer-textarea"
          onChange={(event) => onValueChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={researchMode ? "What should I research?" : "How can I help today?"}
          ref={textareaRef}
          rows={1}
          value={value}
        />
        <div className="composer-actions">
          <div className="composer-left-actions">
            <div className="attach-menu-anchor" ref={attachMenuRef}>
              <Button
                aria-expanded={menuOpen}
                aria-label="Add files or tools"
                className="composer-plus-button"
                disabled={loading}
                onClick={() => setMenuOpen((open) => !open)}
                size="compactIcon"
                type="button"
                variant="quiet"
              >
                <Plus className="size-5" />
              </Button>
              {menuOpen ? (
                <div className="attach-menu">
                  <div className="attach-menu-group">
                    <div className="attach-menu-group-label">Add</div>
                    <button className="attach-menu-item" onClick={handleAttachFile} type="button">
                      <Paperclip className="attach-menu-icon" />
                      <span>
                        <span className="attach-menu-title">Attach File</span>
                        <span className="attach-menu-note">Images, text, markdown, code</span>
                      </span>
                    </button>
                  </div>

                  <div className="attach-menu-group">
                    <div className="attach-menu-group-label">Context</div>
                    <div
                      className="attach-menu-nested"
                      onFocus={() => setOpenSubmenu("project")}
                      onMouseEnter={() => setOpenSubmenu("project")}
                    >
                      <button
                        className="attach-menu-item"
                        onClick={() => setOpenSubmenu((submenu) => (submenu === "project" ? null : "project"))}
                        type="button"
                      >
                        <FolderPlus className="attach-menu-icon" />
                        <span>
                          <span className="attach-menu-title">Add to Project</span>
                          <span className="attach-menu-note">Use a project boundary</span>
                        </span>
                        <ChevronRight className="ml-auto size-3.5 text-muted-foreground" />
                      </button>
                      {openSubmenu === "project" ? (
                        <div className="attach-submenu">
                          {availableProjects.map((project) => (
                            <button
                              className={cn(
                                "attach-menu-item attach-project-item",
                                project.id === activeProjectId && "active",
                              )}
                              key={project.id}
                              onClick={() => handleSelectProject(project.id)}
                              type="button"
                            >
                              <span className="project-dot" style={{ background: project.color }} />
                              <span className="attach-project-name">{project.name}</span>
                              {project.id === activeProjectId ? <span className="attach-menu-check">Active</span> : null}
                            </button>
                          ))}
                          {availableProjects.length > 0 ? <div className="attach-menu-separator" /> : null}
                          <button className="attach-menu-item" onClick={handleCreateProject} type="button">
                            <Plus className="attach-menu-icon" />
                            New Project
                          </button>
                        </div>
                      ) : null}
                    </div>
                  </div>

                  <div className="attach-menu-group">
                    <div className="attach-menu-group-label">Skills</div>
                    <div
                      className="attach-menu-nested"
                      onFocus={() => setOpenSubmenu("skill")}
                      onMouseEnter={() => setOpenSubmenu("skill")}
                    >
                      <button
                        className="attach-menu-item"
                        onClick={() => setOpenSubmenu("skill")}
                        type="button"
                      >
                        <Sparkles className="attach-menu-icon" />
                        <span>
                          <span className="attach-menu-title">Use Skill</span>
                          <span className="attach-menu-note">Pick a role or workflow</span>
                        </span>
                        <ChevronRight className="ml-auto size-3.5 text-muted-foreground" />
                      </button>
                      {openSubmenu === "skill" ? (
                        <div className="attach-submenu skill-submenu">
                          <div className="skill-picker-search">
                            <Search className="size-3.5" />
                            <input
                              aria-label="Search skills"
                              className="skill-search-input"
                              onChange={(event) => setSkillSearch(event.target.value)}
                              placeholder="Search skills"
                              type="search"
                              value={skillSearch}
                            />
                          </div>
                          <div className="skill-picker-scope" aria-label="Skill invocation scope">
                            {SKILL_SCOPE_OPTIONS.map((scope) => (
                              <button
                                aria-pressed={skillScope === scope.id}
                                className={cn(skillScope === scope.id && "active")}
                                key={scope.id}
                                onClick={() => setSkillScope(scope.id)}
                                title={scope.detail}
                                type="button"
                              >
                                {scope.label}
                              </button>
                            ))}
                          </div>
                          {filteredSkillCommands.map((command) => (
                            <button
                              className="attach-menu-item attach-skill-item skill-picker-row"
                              key={command.command}
                              onClick={() => handleUseSkill(command)}
                              type="button"
                            >
                              <span className="attach-skill-copy">
                                <span className="attach-skill-name">/{command.name}</span>
                                <span className="attach-skill-desc skill-picker-description">{command.description}</span>
                              </span>
                              <span className="skill-picker-safety">Skill</span>
                            </button>
                          ))}
                          {filteredSkillCommands.length === 0 ? (
                            <div className="attach-menu-empty">
                              {skillCommands.length === 0 ? "No skills installed" : "No skills match"}
                            </div>
                          ) : null}
                        </div>
                      ) : null}
                    </div>
                  </div>

                  <div className="attach-menu-group">
                    <div className="attach-menu-group-label">Tools</div>
                    <button className="attach-menu-item" onClick={handleDeepResearch} type="button">
                      <Telescope className="attach-menu-icon" />
                      <span>
                        <span className="attach-menu-title">Deep Research</span>
                        <span className="attach-menu-note">Plan, collect sources, synthesize</span>
                      </span>
                    </button>
                    <button className="attach-menu-item" onClick={handleWebSearch} type="button">
                      <Globe2 className="attach-menu-icon" />
                      <span>
                        <span className="attach-menu-title">Web Search</span>
                        <span className="attach-menu-note">Use fresh public sources</span>
                      </span>
                      {webSearchMode ? <span className="attach-menu-check">On</span> : null}
                    </button>
                  </div>
                </div>
              ) : null}
            </div>
            {activeComposerPills.length > 0 ? (
              <div className="composer-active-pills" aria-label="Active composer context">
                {visibleComposerPills.map((pill) => (
                  <span className="composer-active-pill-slot" key={pill.id}>
                    {pill.element}
                  </span>
                ))}
                {hiddenComposerPillCount > 0 ? (
                  <span className="composer-overflow-chip" title={hiddenComposerPillLabels}>
                    +{hiddenComposerPillCount}
                  </span>
                ) : null}
              </div>
            ) : null}
          </div>
          <div className="composer-right-actions">
            <div className="mode-menu-anchor" ref={modeMenuRef}>
              <button
                aria-expanded={modeMenuOpen}
                className="composer-mode-selector"
                disabled={loading}
                onClick={() => setModeMenuOpen((open) => !open)}
                title="Reasoning mode"
                type="button"
              >
                {selectedMode.label}
              </button>
              {modeMenuOpen ? (
                <div className="mode-menu">
                  <div className="mode-menu-kicker">Mode</div>
                  {COMPOSER_MODES.map((mode) => (
                    <button
                      className={cn("mode-menu-item", selectedMode.id === mode.id && "active")}
                      key={mode.id}
                      onClick={() => {
                        onModeChange?.(mode.id)
                        setModeMenuOpen(false)
                      }}
                      type="button"
                    >
                      <span className="mode-menu-title">{mode.label}</span>
                      <span className="mode-menu-desc">{mode.description}</span>
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
            {loading ? (
              <Button
                aria-label="Stop generation"
                className="stop-button"
                onClick={onStop}
                size="compactIcon"
                title="Stop"
                type="button"
                variant="quiet"
              >
                <Square className="size-4" fill="currentColor" />
              </Button>
            ) : null}
            <div className="composer-submit-slot">
              {canSend ? (
                <Button
                  aria-label={isStreaming ? "Interrupt with message" : "Send message"}
                  className="send-button"
                  disabled={!canSend}
                  onClick={handleSubmit}
                  size="compactIcon"
                  title={isStreaming ? "Interrupt" : "Send message"}
                  type="button"
                >
                  {isStreaming ? <MessageSquarePlus className="size-4" /> : <ArrowUp className="size-4" />}
                </Button>
              ) : (
                <Button
                  aria-label={listening ? "Stop voice input" : "Voice input"}
                  aria-pressed={listening}
                  className={cn("composer-voice-button", listening && "is-listening")}
                  disabled={loading || !voiceSupported}
                  onClick={handleVoiceInput}
                  size="compactIcon"
                  title={voiceSupported ? (listening ? "Listening..." : "Voice input") : "Voice input is not available"}
                  type="button"
                  variant={listening ? "default" : "quiet"}
                >
                  <Mic className="size-5" />
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
      {voiceError ? <div className="composer-error">{voiceError}</div> : null}
    </div>
  )
}

function matchesSlashCommand(command: SlashCommand, slashQuery: string): boolean {
  if (!slashQuery) return true
  const name = command.name.toLowerCase()
  const commandValue = command.command.toLowerCase()
  const description = command.description.toLowerCase()
  return (
    name.includes(slashQuery) ||
    commandValue.includes(slashQuery) ||
    description.includes(slashQuery) ||
    command.params.some((param) => param.toLowerCase().includes(slashQuery))
  )
}

function slashCommandGroup(command: SlashCommand): SlashCommandGroup {
  const haystack = `${command.name} ${command.command} ${command.description} ${command.params.join(" ")}`.toLowerCase()
  for (const [group, terms] of Object.entries(SLASH_GROUP_TERMS)) {
    if (terms.some((term) => haystack.includes(term))) return group as SlashCommandGroup
  }
  if (command.level === "client" || command.level === "server") return "System"
  return "Skills"
}

function slashCommandIcon(command: SlashCommand): string {
  const group = slashCommandGroup(command)
  if (group === "Project") return "P"
  if (group === "Memory") return "M"
  if (group === "Research") return "R"
  if (group === "Developer") return "D"
  if (group === "Skills") return "S"
  return "/"
}

const SKILL_SCOPE_OPTIONS: Array<{ id: SkillInvocationScope; label: string; detail: string }> = [
  { id: "once", label: "Once", detail: "Use this skill for the next message only" },
  { id: "chat", label: "Session", detail: "Keep this skill visible as the working mode for this chat session" },
  { id: "project", label: "Project", detail: "Treat this skill as project-scoped context for this run" },
  { id: "global", label: "Global", detail: "Use as the default preference when you intentionally choose this skill" },
]

function isFileDrag(event: globalThis.DragEvent): boolean {
  return Array.from(event.dataTransfer?.types ?? []).includes("Files")
}
