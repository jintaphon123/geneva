import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { motion } from "framer-motion"
import {
  Archive,
  AlertTriangle,
  ArrowLeft,
  BarChart3,
  ChevronDown,
  ChevronRight,
  Code2,
  CheckCircle2,
  Clock3,
  Copy,
  Eye,
  FileText,
  Folder,
  Upload,
  MoreVertical,
  PauseCircle,
  PlayCircle,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  Trash2,
  X,
} from "lucide-react"

import { BuildSkillModal, SkillDetailModal } from "@/components/SkillModals"
import { Button } from "@/components/ui/button"
import { activateSkill, deleteSkill, fetchSkills, setSkillStatus } from "@/lib/api"
import { fetchSkill, fetchSkillFile, fetchSkillFiles } from "@/lib/api/skill-api"
import { cn } from "@/lib/utils"
import {
  activationBlockedReason,
  canActivateSkill,
  skillDisplaySource,
  skillErrorMessage,
} from "@/lib/skill-state"
import type { SkillInvocationScope, SkillMeta } from "@/types"
import type { SkillFileNode } from "@/lib/api/skill-api"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

type SkillBrowserProps = {
  onBack?: () => void
  backLabel?: string
  onSelectSkill: (trigger: string) => void
  onCreateSkillChat?: () => void
  skills?: SkillMeta[]
  onSkillsChanged?: (skills: SkillMeta[]) => void
}

type SelectedFile = {
  skillName: string
  path: string
  name: string
  content: string
}

type SkillFilter = "discover" | "installed" | "generated" | "review" | "evals" | "builder"

const SKILL_SCOPE_OPTIONS: Array<{ id: SkillInvocationScope; label: string; detail: string }> = [
  { id: "once", label: "Use once", detail: "Apply this skill only to the next message." },
  { id: "chat", label: "Session", detail: "Keep this skill visible as the working mode for this chat session." },
  { id: "project", label: "Project", detail: "Treat this skill as project-scoped context for this run." },
  { id: "global", label: "Global", detail: "Use as the default preference when you intentionally choose this skill." },
]

export function SkillBrowser({
  backLabel = "Chat",
  onBack,
  onSelectSkill,
  onCreateSkillChat,
  skills: externalSkills,
  onSkillsChanged,
}: SkillBrowserProps) {
  const [skills, setSkills] = useState<SkillMeta[]>(externalSkills ?? [])
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(!externalSkills)
  const [menuOpenFor, setMenuOpenFor] = useState<string | null>(null)
  const [detailName, setDetailName] = useState<string | null>(null)
  const [buildOpen, setBuildOpen] = useState(false)
  const [filter, setFilter] = useState<SkillFilter>("discover")
  const [scopeBySkill, setScopeBySkill] = useState<Record<string, SkillInvocationScope>>({})
  const [selectedName, setSelectedName] = useState<string | null>(externalSkills?.[0]?.name ?? null)
  const [error, setError] = useState<string | null>(null)
  const [busyAction, setBusyAction] = useState<string | null>(null)
  const [pendingDelete, setPendingDelete] = useState<SkillMeta | null>(null)
  const [addMenuOpen, setAddMenuOpen] = useState(false)
  const addMenuRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [skillFiles, setSkillFiles] = useState<Record<string, SkillFileNode[]>>({})
  const [selectedFile, setSelectedFile] = useState<SelectedFile | null>(null)
  const [fileViewMode, setFileViewMode] = useState<"visual" | "code">("visual")
  const [mainFileContent, setMainFileContent] = useState<string | null>(null)
  const [builtinCollapsed, setBuiltinCollapsed] = useState(false)
  const [mySkillsCollapsed, setMySkillsCollapsed] = useState(false)

  const loadSkills = useCallback(async () => {
    setLoading(true)
    try {
      const result = await fetchSkills()
      setSkills(result.skills)
      setError(null)
      onSkillsChanged?.(result.skills)
    } catch (caught) {
      setError(skillErrorMessage(caught, "Skills could not sync. Existing skills remain visible."))
    } finally {
      setLoading(false)
    }
  }, [onSkillsChanged])

  useEffect(() => {
    if (externalSkills) {
      setSkills(externalSkills)
    }
  }, [externalSkills])

  useEffect(() => {
    if (!externalSkills) void loadSkills()
  }, [externalSkills, loadSkills])

  useEffect(() => {
    if (!addMenuOpen) return
    function handleClickOutside(event: MouseEvent) {
      if (addMenuRef.current && !addMenuRef.current.contains(event.target as Node)) {
        setAddMenuOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [addMenuOpen])

  const queryFiltered = useMemo(
    () =>
      skills.filter(
        (skill) =>
          skill.name.toLowerCase().includes(query.toLowerCase()) ||
          (skill.description ?? "").toLowerCase().includes(query.toLowerCase()) ||
          skill.status.toLowerCase().includes(query.toLowerCase()) ||
          (skill.source ?? "").toLowerCase().includes(query.toLowerCase()),
      ),
    [query, skills],
  )

  const filtered = useMemo(
    () =>
      queryFiltered.filter((skill) => {
        if (filter === "installed") return skill.status === "active" || skill.status === "disabled"
        if (filter === "generated") return skill.source === "generated" || skill.source === "feedback"
        if (filter === "review") return skill.status === "review" || skill.safety_status === "blocked" || skill.safety_status === "warning"
        if (filter === "evals") return Boolean(skill.eval_cases?.length || skill.feedback_summary?.count || skill.feedback?.length)
        if (filter === "builder") return skill.source === "generated" || skill.source === "feedback" || skill.status === "review"
        return true
      }),
    [filter, queryFiltered],
  )

  const builtinSkills = useMemo(() => filtered.filter((s) => s.source === "builtin" || s.source === "bundled"), [filtered])
  const mySkills = useMemo(() => filtered.filter((s) => s.source !== "builtin" && s.source !== "bundled"), [filtered])
  const recommendedSkills = useMemo(
    () =>
      [...skills]
        .filter((skill) => skill.status === "active")
        .sort((a, b) => {
          const recentA = a.last_used_at ? new Date(a.last_used_at).getTime() : 0
          const recentB = b.last_used_at ? new Date(b.last_used_at).getTime() : 0
          return (b.usage_count ?? 0) - (a.usage_count ?? 0) || recentB - recentA
        })
        .slice(0, 3),
    [skills],
  )

  const selectedSkill = useMemo(() => {
    if (!filtered.length) return null
    return filtered.find((skill) => skill.name === selectedName) ?? filtered[0]
  }, [filtered, selectedName])
  const selectedScope = selectedSkill ? scopeBySkill[selectedSkill.name] ?? "once" : "once"

  useEffect(() => {
    if (selectedSkill?.name) {
      if (!skillFiles[selectedSkill.name]) {
        void fetchSkillFiles(selectedSkill.name)
          .then((result) => setSkillFiles((prev) => ({ ...prev, [selectedSkill.name]: result.files })))
          .catch(() => {})
      }

      setMainFileContent(null)
      void fetchSkill(selectedSkill.name)
        .then((res) => setMainFileContent(res.skill.system_prompt))
        .catch(() => {
          setMainFileContent(null)
        })
    }
  }, [selectedSkill?.name, skillFiles])

  useEffect(() => {
    if (!filtered.length) {
      setSelectedName(null)
      return
    }
    if (!selectedName || !filtered.some((skill) => skill.name === selectedName)) {
      setSelectedName(filtered[0].name)
    }
  }, [filtered, selectedName])

  async function handleDelete(name: string) {
    setBusyAction(`delete:${name}`)
    setError(null)
    try {
      await deleteSkill(name)
      if (selectedName === name) setSelectedName(null)
      setPendingDelete(null)
      setMenuOpenFor(null)
      await loadSkills()
    } catch (caught) {
      setError(skillErrorMessage(caught, `Could not delete /${name}.`))
    } finally {
      setBusyAction(null)
    }
  }

  async function handleActivate(name: string) {
    const skill = skills.find((item) => item.name === name)
    const blockedReason = skill ? activationBlockedReason(skill) : null
    if (blockedReason) {
      setError(blockedReason)
      return
    }
    setBusyAction(`activate:${name}`)
    setError(null)
    try {
      await activateSkill(name)
      setMenuOpenFor(null)
      await loadSkills()
    } catch (caught) {
      setError(skillErrorMessage(caught, `Could not activate /${name}.`))
    } finally {
      setBusyAction(null)
    }
  }

  async function handleStatus(name: string, status: "review" | "active" | "disabled" | "archived") {
    setBusyAction(`${status}:${name}`)
    setError(null)
    try {
      await setSkillStatus(name, status)
      setMenuOpenFor(null)
      await loadSkills()
    } catch (caught) {
      setError(skillErrorMessage(caught, `Could not move /${name} to ${status}.`))
    } finally {
      setBusyAction(null)
    }
  }

  async function handleFileClick(skillName: string, filePath: string, fileName: string) {
    try {
      const result = await fetchSkillFile(skillName, filePath)
      setSelectedFile({ skillName, path: filePath, name: fileName, content: result.content })
      setFileViewMode("visual")
    } catch {
      setError(`Could not load: ${filePath}`)
    }
  }

  return (
    <div className="skill-browser">
      <div className="skill-customize-topbar">
        <div className="skill-customize-title">
          {onBack ? (
            <button className="skill-back-button" onClick={onBack} type="button">
              <ArrowLeft className="size-4" />
              <span>{backLabel}</span>
            </button>
          ) : null}
        </div>
      </div>
      {error ? (
        <div className="skill-notice error" role="alert">
          <AlertTriangle className="size-4" />
          <span>{error}</span>
          <button onClick={() => setError(null)} type="button">
            Dismiss
          </button>
        </div>
      ) : null}
      <div className="skill-workspace">
        <aside className="skill-filter-rail" aria-label="Skill filters">
          <SkillFilterButton active={filter === "discover"} label="Discover" onClick={() => setFilter("discover")} />
          <SkillFilterButton active={filter === "installed"} label="Installed" onClick={() => setFilter("installed")} />
          <SkillFilterButton active={filter === "review"} label="Needs review" onClick={() => setFilter("review")} />
          <SkillFilterButton
            active={filter === "generated"}
            label="Generated"
            onClick={() => setFilter("generated")}
          />
          <SkillFilterButton
            active={filter === "evals"}
            label="Evaluations"
            onClick={() => setFilter("evals")}
          />
          <SkillFilterButton active={filter === "builder"} label="Builder" onClick={() => setFilter("builder")} />

          <div className="skill-recommendation-strip">
            <div className="skill-filter-heading">Suggested</div>
            {recommendedSkills.length ? (
              recommendedSkills.map((skill) => (
                <button
                  key={skill.name}
                  onClick={() => {
                    setSelectedName(skill.name)
                    setFilter("discover")
                  }}
                  type="button"
                >
                  <Sparkles className="size-3.5" />
                  <span>
                    <strong>/{skill.name}</strong>
                    <small>{formatLastUsed(skill.last_used_at)}</small>
                  </span>
                </button>
              ))
            ) : (
              <p>No active skills yet.</p>
            )}
          </div>
        </aside>

        <section className="skill-list-panel" aria-label="Skill list">
          <div className="skill-search-container" style={{ margin: '16px', background: 'color-mix(in srgb, var(--card) 40%, transparent)', borderRadius: '8px', border: '1px solid color-mix(in srgb, var(--border) 40%, transparent)', padding: '0 12px' }}>
            <Search className="size-4 skill-search-icon" style={{ opacity: 0.5 }} />
            <input
              className="skill-main-search"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search skills..."
              value={query}
              style={{ paddingLeft: '8px', fontSize: '14px', height: '40px', width: '100%' }}
            />
            {query ? (
              <button aria-label="Clear search" className="skill-search-clear" onClick={() => setQuery("")} type="button">
                <X className="size-3" />
              </button>
            ) : null}
            <div className="skill-add-dropdown-wrapper" ref={addMenuRef} style={{ marginLeft: '12px' }}>
              <button
                aria-label="Add skill"
                className="skill-heading-icon-btn"
                onClick={() => setAddMenuOpen((o) => !o)}
                type="button"
              >
                <Plus className="size-4" />
              </button>
              {addMenuOpen ? (
                <div className="skill-add-dropdown">
                  <button
                    onClick={() => {
                      setAddMenuOpen(false)
                      onCreateSkillChat?.()
                    }}
                    type="button"
                  >
                    <Sparkles className="size-3.5" />
                    Create with Geneva
                  </button>
                  <button
                    onClick={() => {
                      setBuildOpen(true)
                      setAddMenuOpen(false)
                    }}
                    type="button"
                  >
                    <FileText className="size-3.5" />
                    Write Skill Instruction
                  </button>
                  <button
                    onClick={() => {
                      fileInputRef.current?.click()
                      setAddMenuOpen(false)
                    }}
                    type="button"
                  >
                    <Upload className="size-3.5" />
                    Upload a Skill
                  </button>
                </div>
              ) : null}
            </div>
          </div>

          <div className="skill-list-content">
            {builtinSkills.length > 0 ? (
              <div className="skill-list-group">
                <button className="skill-group-header" onClick={() => setBuiltinCollapsed(o => !o)} type="button">
                  {builtinCollapsed ? <ChevronRight className="size-4" /> : <ChevronDown className="size-4" />}
                  <span>Built-in Skills</span>
                </button>
                {!builtinCollapsed && (
                  <div className="skill-list">
                    {builtinSkills.map((skill, index) => (
                      <motion.div
                      animate={{ opacity: 1, y: 0 }}
                      className={cn("skill-list-row", selectedSkill?.name === skill.name && "selected")}
                      initial={{ opacity: 0, y: 6 }}
                      key={skill.name}
                      transition={{ delay: index * 0.015, duration: 0.16 }}
                    >
                      <button
                        className={cn("skill-list-main", skill.status !== "active" && "inactive")}
                        onClick={() => {
                          setSelectedName(skill.name)
                          setSelectedFile(null)
                          if (!skillFiles[skill.name]) {
                            void fetchSkillFiles(skill.name)
                              .then((result) =>
                                setSkillFiles((prev) => ({ ...prev, [skill.name]: result.files })),
                              )
                              .catch(() => { })
                          }
                        }}
                        type="button"
                      >
                        <FileText className="size-4 skill-list-icon" />
                        <h4 className="skill-card-name" style={{ flex: 1 }}>{skill.name}</h4>
                        <span className="skill-builtin-badge">Built-in</span>
                        {skillFiles[skill.name] && skillFiles[skill.name].length > 0 ? (
                          <ChevronDown className="size-4" style={{ color: "var(--muted-foreground)", opacity: 0.5 }} />
                        ) : null}
                      </button>
                      <button
                        className="skill-card-menu"
                        onClick={() => setMenuOpenFor((current) => (current === skill.name ? null : skill.name))}
                        title="Skill options"
                        type="button"
                      >
                        <MoreVertical className="size-4" />
                      </button>
                      {menuOpenFor === skill.name ? (
                        <SkillActionMenu
                          canActivate={canActivateSkill(skill)}
                          onActivate={() => void handleActivate(skill.name)}
                          onArchive={() => void handleStatus(skill.name, "archived")}
                          onDelete={() => {
                            setPendingDelete(skill)
                            setMenuOpenFor(null)
                          }}
                          onDisable={() => void handleStatus(skill.name, "disabled")}
                          onView={() => {
                            setDetailName(skill.name)
                            setMenuOpenFor(null)
                          }}
                          skill={skill}
                        />
                      ) : null}
                      {selectedSkill?.name === skill.name && skillFiles[skill.name] && skillFiles[skill.name].length > 0 ? (
                        <SkillFileTree
                          files={skillFiles[skill.name]}
                          onFileClick={handleFileClick}
                          selectedPath={selectedFile?.skillName === skill.name ? selectedFile.path : null}
                          skillName={skill.name}
                        />
                      ) : null}
                    </motion.div>
                  ))}
                </div>
                )}
              </div>
            ) : null}

            {(mySkills.length > 0 || builtinSkills.length === 0) ? (
              <div className="skill-list-group">
                <button className="skill-group-header" onClick={() => setMySkillsCollapsed(o => !o)} type="button">
                  {mySkillsCollapsed ? <ChevronRight className="size-4" /> : <ChevronDown className="size-4" />}
                  <span>My Skills</span>
                </button>
                {!mySkillsCollapsed && <div className="skill-list">
                  {loading ? <p className="skill-empty">Loading skills...</p> : null}
                  {!loading && mySkills.length === 0 && builtinSkills.length === 0 ? (
                    <div className="skill-empty-state">
                      <Sparkles className="size-5" />
                      <p>{skills.length === 0 ? "No skills installed yet" : "No skills match your search"}</p>
                    </div>
                  ) : null}
                  {mySkills.map((skill, index) => (
                    <motion.div
                      animate={{ opacity: 1, y: 0 }}
                      className={cn("skill-list-row", selectedSkill?.name === skill.name && "selected")}
                      initial={{ opacity: 0, y: 6 }}
                      key={skill.name}
                      transition={{ delay: index * 0.015, duration: 0.16 }}
                    >
                      <button
                        className={cn("skill-list-main", skill.status !== "active" && "inactive")}
                        onClick={() => {
                          setSelectedName(skill.name)
                          setSelectedFile(null)
                          if (!skillFiles[skill.name]) {
                            void fetchSkillFiles(skill.name)
                              .then((result) =>
                                setSkillFiles((prev) => ({ ...prev, [skill.name]: result.files })),
                              )
                              .catch(() => { })
                          }
                        }}
                        type="button"
                      >
                        <FileText className="size-4 skill-list-icon" />
                        <h4 className="skill-card-name" style={{ flex: 1 }}>{skill.name}</h4>
                        {skillFiles[skill.name] && skillFiles[skill.name].length > 0 ? (
                          <ChevronDown className="size-4" style={{ color: "var(--muted-foreground)", opacity: 0.5 }} />
                        ) : null}
                      </button>
                      <button
                        className="skill-card-menu"
                        onClick={() => setMenuOpenFor((current) => (current === skill.name ? null : skill.name))}
                        title="Skill options"
                        type="button"
                      >
                        <MoreVertical className="size-4" />
                      </button>
                      {menuOpenFor === skill.name ? (
                        <SkillActionMenu
                          canActivate={canActivateSkill(skill)}
                          onActivate={() => void handleActivate(skill.name)}
                          onArchive={() => void handleStatus(skill.name, "archived")}
                          onDelete={() => {
                            setPendingDelete(skill)
                            setMenuOpenFor(null)
                          }}
                          onDisable={() => void handleStatus(skill.name, "disabled")}
                          onView={() => {
                            setDetailName(skill.name)
                            setMenuOpenFor(null)
                          }}
                          skill={skill}
                        />
                      ) : null}
                      {selectedSkill?.name === skill.name && skillFiles[skill.name] && skillFiles[skill.name].length > 0 ? (
                        <SkillFileTree
                          files={skillFiles[skill.name]}
                          onFileClick={handleFileClick}
                          selectedPath={selectedFile?.skillName === skill.name ? selectedFile.path : null}
                          skillName={skill.name}
                        />
                      ) : null}
                    </motion.div>
                  ))}
                </div>}
              </div>
            ) : null}
          </div>
        </section>

        <aside className="skill-detail-panel" aria-label="Skill detail panel">
          {selectedFile ? (
            <SkillFileViewer
              file={selectedFile}
              mode={fileViewMode}
              onClose={() => setSelectedFile(null)}
              onModeChange={setFileViewMode}
            />
          ) : selectedSkill ? (
            <>
              <div className="skill-detail-header-row">
                <h3 className="skill-detail-name">{selectedSkill.name}</h3>
                <div className="skill-detail-header-controls">
                  <button
                    aria-label={selectedSkill.status === "active" ? `Disable ${selectedSkill.name}` : `Activate ${selectedSkill.name}`}
                    className={cn("skill-activation-switch", selectedSkill.status === "active" && "on")}
                    disabled={busyAction !== null || (selectedSkill.status !== "active" && !canActivateSkill(selectedSkill))}
                    onClick={() =>
                      void (selectedSkill.status === "active"
                        ? handleStatus(selectedSkill.name, "disabled")
                        : handleActivate(selectedSkill.name))
                    }
                    type="button"
                  >
                    <span />
                  </button>
                  <button
                    className="skill-heading-icon-btn"
                    onClick={() => setDetailName(selectedSkill.name)}
                    title="More details"
                    type="button"
                  >
                    <MoreVertical className="size-4" />
                  </button>
                </div>
              </div>

              <div className="skill-detail-meta-row" style={{ display: 'flex', gap: '40px', marginBottom: '24px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ color: 'var(--muted-foreground)', fontSize: '11px' }}>Added by</span>
                  <span className="skill-meta-value" style={{ fontSize: '13px' }}>{skillDisplaySource(selectedSkill)}</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ color: 'var(--muted-foreground)', fontSize: '11px' }}>Trigger</span>
                  <span className="skill-meta-value" style={{ fontSize: '13px' }}>{selectedSkill.command}</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ color: 'var(--muted-foreground)', fontSize: '11px' }}>Safety</span>
                  <span className="skill-meta-value" style={{ fontSize: '13px' }}>{skillSafetyLabel(selectedSkill)}</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ color: 'var(--muted-foreground)', fontSize: '11px' }}>Recent</span>
                  <span className="skill-meta-value" style={{ fontSize: '13px' }}>{formatLastUsed(selectedSkill.last_used_at)}</span>
                </div>
              </div>

              <div className="skill-detail-desc-title">
                Description
                <span style={{ opacity: 0.6, fontSize: '11px', border: '1px solid var(--muted-foreground)', borderRadius: '50%', width: 14, height: 14, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>i</span>
              </div>
              <p className="skill-detail-panel-desc">{selectedSkill.description || "No description provided yet."}</p>

              <div className="skill-scope-card">
                <div>
                  <span className="skill-scope-kicker">Invocation scope</span>
                  <strong>{scopeLabel(selectedScope)}</strong>
                  <p>{scopeDetail(selectedScope)}</p>
                </div>
                <SkillScopeSelector
                  onChange={(scope) =>
                    setScopeBySkill((current) => ({ ...current, [selectedSkill.name]: scope }))
                  }
                  scope={selectedScope}
                />
              </div>

              <div className="skill-capability-row">
                <span><ShieldCheck className="size-3.5" />{skillSafetyLabel(selectedSkill)}</span>
                <span><BarChart3 className="size-3.5" />{selectedSkill.usage_count ?? 0} runs</span>
                <span><Clock3 className="size-3.5" />{formatLastUsed(selectedSkill.last_used_at)}</span>
              </div>

              <button
                className="skill-run-button"
                disabled={selectedSkill.status !== "active" || !selectedSkill.enabled}
                onClick={() => onSelectSkill(`${selectedSkill.command} `)}
                type="button"
              >
                <PlayCircle className="size-4" />
                Use /{selectedSkill.name}
              </button>
              
              <div className="skill-detail-divider" />

              <div className="skill-detail-card">
                <div className="skill-file-viewer-actions" style={{ position: 'absolute', top: 12, right: 12 }}>
                  <button 
                    className={cn("skill-view-toggle-btn", fileViewMode === "visual" && "active")}
                    onClick={() => setFileViewMode("visual")}
                  >
                    <Eye className="size-3.5" />
                  </button>
                  <button 
                    className={cn("skill-view-toggle-btn", fileViewMode === "code" && "active")}
                    onClick={() => setFileViewMode("code")}
                  >
                    <Code2 className="size-3.5" />
                  </button>
                </div>
                <div className="skill-file-content" style={{ padding: '32px' }}>
                  <div className="skill-file-markdown">
                    {mainFileContent ? (
                      fileViewMode === "visual" ? (
                        <div className="prose prose-invert max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {mainFileContent.replace(/^---\n[\s\S]*?\n---\n/, '')}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', margin: 0 }}>
                          {mainFileContent}
                        </pre>
                      )
                    ) : (
                      <>
                        <h2>{selectedSkill.name}</h2>
                        <p>{selectedSkill.description}</p>
                        <br />
                        <h3>Triggers</h3>
                        <ul>
                        {selectedSkill.triggers.length ? (
                          selectedSkill.triggers.map((trigger) => <li key={trigger}><code>{trigger}</code></li>)
                        ) : (
                          <li><code>{selectedSkill.command}</code></li>
                        )}
                        </ul>
                      </>
                    )}
                  </div>
                </div>
              </div>

              <div className="skill-detail-panel-actions">
                <Button
                  disabled={selectedSkill.status !== "active" || !selectedSkill.enabled}
                  onClick={() => onSelectSkill(`${selectedSkill.command} `)}
                  type="button"
                >
                  <PlayCircle className="size-4" />
                  Use skill
                </Button>
                {selectedSkill.status !== "active" && canActivateSkill(selectedSkill) ? (
                  <Button disabled={busyAction !== null} onClick={() => void handleActivate(selectedSkill.name)} type="button" variant="subtle">
                    <CheckCircle2 className="size-4" />
                    Activate
                  </Button>
                ) : null}
                {selectedSkill.status === "active" ? (
                  <Button
                    disabled={busyAction !== null}
                    onClick={() => void handleStatus(selectedSkill.name, "disabled")}
                    type="button"
                    variant="subtle"
                  >
                    <PauseCircle className="size-4" />
                    Disable
                  </Button>
                ) : null}
                <Button onClick={() => setDetailName(selectedSkill.name)} type="button" variant="subtle">
                  <Eye className="size-4" />
                  Details
                </Button>
              </div>
            </>
          ) : (
            <div className="skill-detail-empty">Select a skill to inspect activation, safety, triggers, and history.</div>
          )}
        </aside>
      </div>
      <input
        accept=".md"
        onChange={() => {
          setError("Skill file upload coming soon. Use Create with Geneva for now.")
        }}
        ref={fileInputRef}
        style={{ display: "none" }}
        type="file"
      />
      {detailName ? <SkillDetailModal name={detailName} onClose={() => setDetailName(null)} /> : null}
      {pendingDelete ? (
        <DeleteSkillModal
          busy={busyAction === `delete:${pendingDelete.name}`}
          onCancel={() => setPendingDelete(null)}
          onConfirm={() => void handleDelete(pendingDelete.name)}
          skill={pendingDelete}
        />
      ) : null}
      {buildOpen ? (
        <BuildSkillModal
          onClose={() => setBuildOpen(false)}
          onGenerated={() => void loadSkills()}
          onSaved={() => {
            setBuildOpen(false)
            void loadSkills()
          }}
        />
      ) : null}
    </div>
  )
}

function DeleteSkillModal({
  busy,
  onCancel,
  onConfirm,
  skill,
}: {
  busy: boolean
  onCancel: () => void
  onConfirm: () => void
  skill: SkillMeta
}) {
  return (
    <div className="skill-modal-backdrop">
      <section aria-label="Delete skill confirmation" aria-modal="true" className="skill-modal skill-delete-modal" role="dialog">
        <button aria-label="Close delete skill confirmation" className="skill-modal-close" disabled={busy} onClick={onCancel} type="button">
          <X className="size-4" />
        </button>
        <div className="skill-delete-title">
          <span className="skill-delete-icon">
            <Trash2 className="size-4" />
          </span>
          <div>
            <h3>Delete skill?</h3>
            <p className="skill-modal-desc">
              /{skill.name} will be removed from the control plane and disappear from slash commands after the next sync.
            </p>
          </div>
        </div>
        <div className="skill-delete-summary">
          <span>{skill.status}</span>
          <span>{skill.safety_status ?? "passed"}</span>
          <span>{skillDisplaySource(skill)}</span>
        </div>
        <div className="skill-modal-actions">
          <Button disabled={busy} onClick={onCancel} type="button" variant="subtle">
            Cancel
          </Button>
          <Button disabled={busy} onClick={onConfirm} type="button">
            <Trash2 className="size-4" />
            {busy ? "Deleting..." : "Delete skill"}
          </Button>
        </div>
      </section>
    </div>
  )
}

function SkillFileTree({
  files,
  onFileClick,
  selectedPath,
  skillName,
  depth = 0,
}: {
  files: SkillFileNode[]
  onFileClick: (skillName: string, path: string, name: string) => Promise<void>
  selectedPath: string | null
  skillName: string
  depth?: number
}) {
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set())

  return (
    <div className="skill-tree-children">
      {files.map((node) => (
        <div
          key={node.path}
          className="skill-tree-node"
          style={{ paddingLeft: depth * 12 + 28 }}
        >
          {node.type === "dir" ? (
            <>
              <button
                className="skill-tree-dir"
                onClick={() =>
                  setExpandedDirs((prev) => {
                    const next = new Set(prev)
                    if (next.has(node.path)) next.delete(node.path)
                    else next.add(node.path)
                    return next
                  })
                }
                type="button"
              >
                {expandedDirs.has(node.path) ? <ChevronDown className="size-3" /> : <ChevronRight className="size-3" />}
                <Folder className="size-3.5" />
                <span>{node.name}</span>
              </button>
              {expandedDirs.has(node.path) && node.children ? (
                <SkillFileTree
                  depth={depth + 1}
                  files={node.children}
                  onFileClick={onFileClick}
                  selectedPath={selectedPath}
                  skillName={skillName}
                />
              ) : null}
            </>
          ) : (
            <button
              className={cn("skill-tree-file", selectedPath === node.path && "selected")}
              onClick={() => void onFileClick(skillName, node.path, node.name)}
              type="button"
            >
              <FileText className="size-3.5" />
              <span>{node.name}</span>
            </button>
          )}
        </div>
      ))}
    </div>
  )
}

function SkillFileViewer({
  file,
  mode,
  onClose,
  onModeChange,
}: {
  file: SelectedFile
  mode: "visual" | "code"
  onClose: () => void
  onModeChange: (mode: "visual" | "code") => void
}) {
  const isMarkdown = file.name.endsWith(".md")

  return (
    <div className="skill-file-viewer">
      <div className="skill-file-viewer-header">
        <button className="skill-back-button skill-file-back" onClick={onClose} type="button">
          <ArrowLeft className="size-4" />
        </button>
        <span className="skill-file-viewer-name">{file.name}</span>
        <div className="skill-file-viewer-actions">
          {isMarkdown ? (
            <>
              <button
                aria-label="Preview"
                className={cn("skill-view-toggle-btn", mode === "visual" && "active")}
                onClick={() => onModeChange("visual")}
                title="Preview"
                type="button"
              >
                <Eye className="size-4" />
              </button>
              <button
                aria-label="Raw"
                className={cn("skill-view-toggle-btn", mode === "code" && "active")}
                onClick={() => onModeChange("code")}
                title="Raw"
                type="button"
              >
                <Code2 className="size-4" />
              </button>
            </>
          ) : null}
          <button
            aria-label="Copy content"
            className="skill-view-toggle-btn"
            onClick={() => void navigator.clipboard.writeText(file.content)}
            title="Copy"
            type="button"
          >
            <Copy className="size-4" />
          </button>
        </div>
      </div>
      <div className="skill-file-content">
        {isMarkdown && mode === "visual" ? (
          <div className="markdown-body skill-file-markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{file.content}</ReactMarkdown>
          </div>
        ) : (
          <pre className="skill-file-raw">{file.content}</pre>
        )}
      </div>
    </div>
  )
}

function SkillFilterButton({
  active,
  label,
  onClick,
}: {
  active: boolean
  label: string
  onClick: () => void
}) {
  return (
    <button className={cn("skill-filter-button", active && "active")} onClick={onClick} type="button">
      <span>{label}</span>
    </button>
  )
}

function SkillScopeSelector({
  onChange,
  scope,
}: {
  onChange: (scope: SkillInvocationScope) => void
  scope: SkillInvocationScope
}) {
  return (
    <div className="skill-scope-selector" aria-label="Skill invocation scope">
      {SKILL_SCOPE_OPTIONS.map((option) => (
        <button
          aria-pressed={scope === option.id}
          className={cn(scope === option.id && "active")}
          key={option.id}
          onClick={() => onChange(option.id)}
          title={option.detail}
          type="button"
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}

function skillSafetyLabel(skill: SkillMeta): string {
  if (skill.safety_status === "blocked") return "Blocked"
  if (skill.safety_status === "warning") return "Needs review"
  return "Safety passed"
}

function formatLastUsed(value?: string | null): string {
  if (!value) return "Not used yet"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "Recently used"
  const deltaMs = Date.now() - date.getTime()
  const dayMs = 86_400_000
  if (deltaMs < 60_000) return "Just now"
  if (deltaMs < dayMs) return "Today"
  const days = Math.round(deltaMs / dayMs)
  if (days === 1) return "Yesterday"
  if (days < 30) return `${days} days ago`
  return date.toLocaleDateString([], { month: "short", day: "numeric" })
}

function scopeLabel(scope: SkillInvocationScope): string {
  return SKILL_SCOPE_OPTIONS.find((option) => option.id === scope)?.label ?? "Use once"
}

function scopeDetail(scope: SkillInvocationScope): string {
  return SKILL_SCOPE_OPTIONS.find((option) => option.id === scope)?.detail ?? SKILL_SCOPE_OPTIONS[0].detail
}

function SkillActionMenu({
  canActivate,
  onActivate,
  onArchive,
  onDelete,
  onDisable,
  onView,
  skill,
}: {
  canActivate: boolean
  onActivate: () => void
  onArchive: () => void
  onDelete: () => void
  onDisable: () => void
  onView: () => void
  skill: SkillMeta
}) {
  return (
    <div className="skill-card-popover">
      <button onClick={onView} type="button">
        <Eye className="size-3.5" />
        View details
      </button>
      {skill.status !== "active" && canActivate ? (
        <button onClick={onActivate} type="button">
          <CheckCircle2 className="size-3.5" />
          Activate
        </button>
      ) : null}
      {skill.status === "active" ? (
        <button onClick={onDisable} type="button">
          <PauseCircle className="size-3.5" />
          Disable
        </button>
      ) : null}
      {skill.status !== "archived" ? (
        <button onClick={onArchive} type="button">
          <Archive className="size-3.5" />
          Archive
        </button>
      ) : null}
      <button className="danger" onClick={onDelete} type="button">
        <Trash2 className="size-3.5" />
        Delete
      </button>
    </div>
  )
}
