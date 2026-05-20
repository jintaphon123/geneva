import { useCallback, useEffect, useMemo, useState } from "react"
import {
  ArrowLeft,
  CheckCircle2,
  Clock3,
  Copy,
  FileText,
  Layers,
  Link2,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react"

import { MarkdownRenderer } from "@/components/ChatMarkdown"
import { Button } from "@/components/ui/button"
import { deleteArtifact, fetchArtifact, fetchArtifacts, fetchResearchRuns } from "@/lib/api"
import { cn } from "@/lib/utils"
import type { ArtifactDetail, ArtifactRecord, Project, ResearchRun, ResearchSource } from "@/types"

type ArtifactFilter = "all" | "research_report" | "document_preview" | "tool_output" | "screenshot" | "citation_map"

type ParsedArtifactContent = {
  text: string
  query?: string
  runId?: string
  projectId?: string | null
  sessionId?: string | null
  sources: ResearchSource[]
  qualityScore?: Record<string, unknown>
}

const FILTERS: Array<{ id: ArtifactFilter; label: string }> = [
  { id: "all", label: "All" },
  { id: "research_report", label: "Research reports" },
  { id: "document_preview", label: "Documents" },
  { id: "tool_output", label: "Tool output" },
  { id: "screenshot", label: "Screenshots" },
  { id: "citation_map", label: "Citation maps" },
]

export function ArtifactsSurface({
  activeProject,
  onBack,
  projects,
  sessionId,
}: {
  activeProject: Project | null
  onBack: () => void
  projects: Project[]
  sessionId: string | null
}) {
  const [artifacts, setArtifacts] = useState<ArtifactRecord[]>([])
  const [researchRuns, setResearchRuns] = useState<ResearchRun[]>([])
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | null>(null)
  const [selectedDetail, setSelectedDetail] = useState<ArtifactDetail | null>(null)
  const [filter, setFilter] = useState<ArtifactFilter>("all")
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const projectNames = useMemo(() => new Map(projects.map((project) => [project.id, project.name])), [projects])

  const runsByArtifact = useMemo(() => {
    const map = new Map<string, ResearchRun>()
    for (const run of researchRuns) {
      if (run.artifact_id) map.set(run.artifact_id, run)
    }
    return map
  }, [researchRuns])

  const loadArtifacts = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [artifactResult, runResult] = await Promise.all([
        fetchArtifacts({ limit: 80 }),
        fetchResearchRuns({ limit: 80 }),
      ])
      setArtifacts(artifactResult)
      setResearchRuns(runResult.runs)
      setSelectedArtifactId((current) => current ?? artifactResult[0]?.artifact_id ?? null)
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Artifacts could not load")
      setArtifacts([])
      setResearchRuns([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadArtifacts()
  }, [loadArtifacts])

  useEffect(() => {
    if (!selectedArtifactId) {
      setSelectedDetail(null)
      return
    }
    const controller = new AbortController()
    setDetailLoading(true)
    void fetchArtifact(selectedArtifactId, controller.signal)
      .then(setSelectedDetail)
      .catch((detailError) => {
        if (detailError instanceof DOMException && detailError.name === "AbortError") return
        setSelectedDetail(null)
      })
      .finally(() => setDetailLoading(false))
    return () => controller.abort()
  }, [selectedArtifactId])

  const visibleArtifacts = useMemo(() => {
    const cleanQuery = query.trim().toLowerCase()
    return artifacts.filter((artifact) => {
      if (filter !== "all" && artifact.type !== filter) return false
      const run = runsByArtifact.get(artifact.artifact_id)
      const title = artifactTitle(artifact, run).toLowerCase()
      const labels = [artifactTypeLabel(artifact.type), run?.query, run?.status, artifact.session_id]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
      return !cleanQuery || `${title} ${labels}`.includes(cleanQuery)
    })
  }, [artifacts, filter, query, runsByArtifact])

  const selectedArtifact = useMemo(
    () => artifacts.find((artifact) => artifact.artifact_id === selectedArtifactId) ?? null,
    [artifacts, selectedArtifactId],
  )
  const selectedRun = selectedArtifact?.artifact_id ? runsByArtifact.get(selectedArtifact.artifact_id) ?? null : null
  const parsed = parseArtifactContent(selectedDetail, selectedRun)
  const sourceTrace = selectedRun?.sources?.length ? selectedRun.sources : parsed.sources
  const detailProjectName = selectedRun?.project_id
    ? projectNames.get(selectedRun.project_id) ?? selectedRun.project_id
    : parsed.projectId
      ? projectNames.get(parsed.projectId) ?? parsed.projectId
      : null

  async function handleCopyText() {
    const text = parsed.text || selectedDetail?.content || ""
    if (!text.trim()) return
    await navigator.clipboard.writeText(text)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1400)
  }

  async function handleDeleteArtifact() {
    if (!selectedArtifactId) return
    const confirmed = window.confirm("Delete this artifact?")
    if (!confirmed) return
    await deleteArtifact(selectedArtifactId)
    setSelectedArtifactId(null)
    setSelectedDetail(null)
    await loadArtifacts()
  }

  return (
    <section className="artifacts-surface" aria-label="Artifacts">
      <header className="artifacts-surface-header">
        <div className="artifacts-title-group">
          <Button aria-label="Back to chat" onClick={onBack} size="compactIcon" variant="quiet">
            <ArrowLeft className="size-4" />
          </Button>
          <div>
            <p>Artifacts</p>
            <h1>Durable work</h1>
          </div>
        </div>
        <div className="artifacts-header-actions">
          {activeProject ? (
            <span className="artifacts-context-pill">
              <span style={{ background: activeProject.color }} />
              {activeProject.name}
            </span>
          ) : null}
          {sessionId ? <span className="artifacts-context-pill muted">Current chat available</span> : null}
          <Button onClick={() => void loadArtifacts()} variant="subtle">
            <RefreshCw className={cn("size-4", loading && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </header>

      <div className="artifacts-toolbar">
        <div className="artifacts-search">
          <Search className="size-4" />
          <input
            aria-label="Search artifacts"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search reports, documents, and traces"
            value={query}
          />
        </div>
        <div className="artifacts-filter-row" aria-label="Artifact filters">
          {FILTERS.map((item) => (
            <button
              className={cn("artifacts-filter-chip", filter === item.id && "active")}
              key={item.id}
              onClick={() => setFilter(item.id)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <div className="artifacts-error" role="status">
          {error}
        </div>
      ) : null}

      <div className="artifacts-layout">
        <aside className="artifacts-list" aria-busy={loading}>
          {loading ? (
            <div className="artifacts-empty-state">
              <RefreshCw className="size-4 animate-spin" />
              <p>Loading artifacts...</p>
            </div>
          ) : null}
          {!loading && visibleArtifacts.length === 0 ? (
            <div className="artifacts-empty-state">
              <Layers className="size-5" />
              <strong>No durable outputs yet</strong>
              <p>Deep Research reports, document previews, and tool outputs will appear here after Geneva saves them.</p>
            </div>
          ) : null}
          {visibleArtifacts.map((artifact) => {
            const run = runsByArtifact.get(artifact.artifact_id)
            return (
              <button
                className={cn("artifact-list-row", artifact.artifact_id === selectedArtifactId && "active")}
                key={artifact.artifact_id}
                onClick={() => setSelectedArtifactId(artifact.artifact_id)}
                type="button"
              >
                <span className="artifact-list-icon">
                  <FileText className="size-4" />
                </span>
                <span className="artifact-list-copy">
                  <strong>{artifactTitle(artifact, run)}</strong>
                  <span>{artifactTypeLabel(artifact.type)} · {formatArtifactDate(artifact.created_at)}</span>
                </span>
                {run?.status === "completed" ? <CheckCircle2 className="size-3.5 artifact-list-status" /> : null}
              </button>
            )
          })}
        </aside>

        <article className="artifact-detail">
          {!selectedArtifact ? (
            <div className="artifact-detail-empty">
              <Layers className="size-6" />
              <p>Select an artifact to inspect its report, sources, and origin.</p>
            </div>
          ) : (
            <>
              <div className="artifact-detail-header">
                <div>
                  <span className="artifact-type-pill">{artifactTypeLabel(selectedArtifact.type)}</span>
                  <h2>{artifactTitle(selectedArtifact, selectedRun)}</h2>
                  <div className="artifact-detail-meta">
                    <span><Clock3 className="size-3.5" /> {formatArtifactDate(selectedArtifact.created_at)}</span>
                    {detailProjectName ? <span><Layers className="size-3.5" /> {detailProjectName}</span> : null}
                    {selectedRun?.session_id ? <span><Link2 className="size-3.5" /> Source conversation</span> : null}
                  </div>
                </div>
                <div className="artifact-detail-actions">
                  <Button disabled={detailLoading || !(parsed.text || selectedDetail?.content)} onClick={handleCopyText} variant="subtle">
                    <Copy className="size-4" />
                    {copied ? "Copied" : "Copy text"}
                  </Button>
                  <Button aria-label="Delete artifact" onClick={() => void handleDeleteArtifact()} size="compactIcon" variant="quiet">
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              </div>

              {detailLoading ? (
                <div className="artifact-detail-loading">
                  <RefreshCw className="size-4 animate-spin" />
                  Loading artifact...
                </div>
              ) : (
                <>
                  {selectedRun ? (
                    <div className="artifact-run-summary">
                      <span>{selectedRun.mode === "deep" ? "Deep Research" : selectedRun.mode}</span>
                      <span>{selectedRun.status}</span>
                      {selectedRun.artifact_id ? <span>Saved as report artifact</span> : null}
                    </div>
                  ) : null}

                  <section className="artifact-report-body">
                    {parsed.text ? (
                      <MarkdownRenderer onOpenArtifactPanel={noopOpenArtifact} onShowCodePreview={noopCodePreview}>
                        {parsed.text}
                      </MarkdownRenderer>
                    ) : (
                      <pre>{selectedDetail?.content || "No readable content stored for this artifact."}</pre>
                    )}
                  </section>

                  <section className="artifact-source-trace">
                    <div className="artifact-section-heading">
                      <h3>Source trace</h3>
                      <span>{sourceTrace.length} sources</span>
                    </div>
                    {sourceTrace.length ? (
                      <div className="artifact-source-list">
                        {sourceTrace.map((source, index) => (
                          <a
                            className="artifact-source-row"
                            href={source.url || undefined}
                            key={`${source.source_id}-${index}`}
                            rel="noreferrer"
                            target={source.url ? "_blank" : undefined}
                          >
                            <span>{source.source_id || `S${index + 1}`}</span>
                            <strong>{source.title || "Untitled source"}</strong>
                            <small>{source.publisher || source.url || "No source URL"}</small>
                          </a>
                        ))}
                      </div>
                    ) : (
                      <p className="artifact-muted">No sources were attached to this artifact.</p>
                    )}
                  </section>
                </>
              )}
            </>
          )}
        </article>
      </div>
    </section>
  )
}

export function artifactTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    citation_map: "Citation map",
    document_preview: "Document preview",
    research_report: "Research report",
    research_trace: "Research trace",
    screenshot: "Screenshot",
    tool_output: "Tool output",
  }
  return labels[type] ?? humanizeType(type)
}

function artifactTitle(artifact: ArtifactRecord, run?: ResearchRun | null): string {
  if (run?.query?.trim()) return run.query.trim()
  return `${artifactTypeLabel(artifact.type)} from ${formatArtifactDate(artifact.created_at)}`
}

function parseArtifactContent(detail: ArtifactDetail | null, run?: ResearchRun | null): ParsedArtifactContent {
  const raw = detail?.content || ""
  const fallbackText = run?.final_text || raw
  if (!raw.trim()) {
    return {
      text: fallbackText,
      query: run?.query,
      runId: run?.id,
      projectId: run?.project_id,
      sessionId: run?.session_id,
      sources: run?.sources ?? [],
      qualityScore: run?.metadata?.quality_score as Record<string, unknown> | undefined,
    }
  }
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>
    const sources = Array.isArray(parsed.sources)
      ? parsed.sources.filter((item): item is ResearchSource => Boolean(item && typeof item === "object"))
      : []
    const qualityScore =
      parsed.quality_score && typeof parsed.quality_score === "object" && !Array.isArray(parsed.quality_score)
        ? (parsed.quality_score as Record<string, unknown>)
        : undefined
    return {
      text: typeof parsed.text === "string" ? parsed.text : fallbackText,
      query: typeof parsed.query === "string" ? parsed.query : run?.query,
      runId: typeof parsed.run_id === "string" ? parsed.run_id : run?.id,
      projectId: typeof parsed.project_id === "string" ? parsed.project_id : run?.project_id,
      sessionId: typeof parsed.session_id === "string" ? parsed.session_id : run?.session_id,
      sources: sources.length ? sources : run?.sources ?? [],
      qualityScore,
    }
  } catch {
    return {
      text: fallbackText,
      query: run?.query,
      runId: run?.id,
      projectId: run?.project_id,
      sessionId: run?.session_id,
      sources: run?.sources ?? [],
      qualityScore: run?.metadata?.quality_score as Record<string, unknown> | undefined,
    }
  }
}

function formatArtifactDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "Unknown date"
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
}

function humanizeType(type: string): string {
  return type
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ")
}

function noopOpenArtifact() {
  return undefined
}

function noopCodePreview() {
  return undefined
}
