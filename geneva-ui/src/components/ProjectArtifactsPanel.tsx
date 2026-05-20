import { useEffect, useMemo, useState } from "react"
import { CheckCircle2, FileText, Layers, RefreshCw } from "lucide-react"

import { artifactTypeLabel } from "@/components/ArtifactsSurface"
import { MarkdownRenderer } from "@/components/ChatMarkdown"
import { fetchArtifact, fetchResearchRuns } from "@/lib/api"
import { cn } from "@/lib/utils"
import type { ArtifactDetail, ResearchRun, ResearchSource } from "@/types"

export function ProjectArtifactsPanel({
  projectId,
  projectName,
}: {
  projectId: string
  projectName: string
}) {
  const [runs, setRuns] = useState<ResearchRun[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [selectedArtifact, setSelectedArtifact] = useState<ArtifactDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    void fetchResearchRuns({ projectId, limit: 40, signal: controller.signal })
      .then((result) => {
        const reportRuns = result.runs.filter((run) => run.artifact_id || run.final_text.trim())
        setRuns(reportRuns)
        setSelectedRunId((current) => current ?? reportRuns[0]?.id ?? null)
      })
      .catch((loadError) => {
        if (loadError instanceof DOMException && loadError.name === "AbortError") return
        setError(loadError instanceof Error ? loadError.message : "Project artifacts could not load")
        setRuns([])
      })
      .finally(() => setLoading(false))
    return () => controller.abort()
  }, [projectId])

  const selectedRun = useMemo(
    () => runs.find((run) => run.id === selectedRunId) ?? null,
    [runs, selectedRunId],
  )

  useEffect(() => {
    if (!selectedRun?.artifact_id) {
      setSelectedArtifact(null)
      return
    }
    const controller = new AbortController()
    setDetailLoading(true)
    void fetchArtifact(selectedRun.artifact_id, controller.signal)
      .then(setSelectedArtifact)
      .catch((detailError) => {
        if (detailError instanceof DOMException && detailError.name === "AbortError") return
        setSelectedArtifact(null)
      })
      .finally(() => setDetailLoading(false))
    return () => controller.abort()
  }, [selectedRun?.artifact_id])

  const parsedReport = parseResearchReport(selectedArtifact, selectedRun)
  const selectedSources = parsedReport.sources.length ? parsedReport.sources : selectedRun?.sources ?? []

  return (
    <div className="project-artifacts-panel">
      <div className="project-artifacts-list" aria-busy={loading}>
        {loading ? (
          <div className="project-artifacts-empty">
            <RefreshCw className="size-4 animate-spin" />
            <span>Loading research reports...</span>
          </div>
        ) : null}
        {error ? (
          <div className="project-artifacts-empty error">
            <span>{error}</span>
          </div>
        ) : null}
        {!loading && !error && runs.length === 0 ? (
          <div className="project-artifacts-empty">
            <Layers className="size-5" />
            <strong>No research reports in {projectName} yet.</strong>
            <p>Run Deep Research while this project is attached, and Geneva will save the completed report here.</p>
          </div>
        ) : null}
        {runs.map((run) => (
          <button
            className={cn("project-artifact-row", run.id === selectedRunId && "active")}
            key={run.id}
            onClick={() => setSelectedRunId(run.id)}
            type="button"
          >
            <FileText className="size-4" />
            <span>
              <strong>{run.query}</strong>
              <small>
                {run.artifact_id ? artifactTypeLabel("research_report") : "Research report draft"} · {formatRunDate(run.updated_at)}
              </small>
            </span>
            {run.status === "completed" ? <CheckCircle2 className="size-3.5" /> : null}
          </button>
        ))}
      </div>

      <div className="project-artifact-detail">
        {!selectedRun ? (
          <div className="project-artifacts-empty">
            <FileText className="size-5" />
            <span>Select a report to preview it.</span>
          </div>
        ) : (
          <>
            <div className="project-artifact-detail-header">
              <span>{selectedRun.status}</span>
              <h3>{selectedRun.query}</h3>
              <p>
                {selectedSources.length} sources · {selectedRun.artifact_id ? "Saved as report artifact" : "Not saved as artifact yet"}
              </p>
            </div>
            {detailLoading ? (
              <div className="project-artifacts-empty">
                <RefreshCw className="size-4 animate-spin" />
                <span>Loading report...</span>
              </div>
            ) : (
              <>
                <div className="project-artifact-report">
                  <MarkdownRenderer onOpenArtifactPanel={noopOpenArtifact} onShowCodePreview={noopCodePreview}>
                    {parsedReport.text || selectedRun.final_text || "No report text is available yet."}
                  </MarkdownRenderer>
                </div>
                <div className="project-artifact-sources">
                  <strong>Source trace</strong>
                  {selectedSources.map((source, index) => (
                    <a
                      href={source.url || undefined}
                      key={`${source.source_id}-${index}`}
                      rel="noreferrer"
                      target={source.url ? "_blank" : undefined}
                    >
                      <span>{source.source_id || `S${index + 1}`}</span>
                      <small>{source.title || source.url || "Untitled source"}</small>
                    </a>
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function parseResearchReport(
  artifact: ArtifactDetail | null,
  run: ResearchRun | null,
): { text: string; sources: ResearchSource[] } {
  const raw = artifact?.content || ""
  if (!raw.trim()) return { text: run?.final_text || "", sources: run?.sources ?? [] }
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>
    return {
      text: typeof parsed.text === "string" ? parsed.text : run?.final_text || raw,
      sources: Array.isArray(parsed.sources)
        ? parsed.sources.filter((item): item is ResearchSource => Boolean(item && typeof item === "object"))
        : run?.sources ?? [],
    }
  } catch {
    return { text: run?.final_text || raw, sources: run?.sources ?? [] }
  }
}

function formatRunDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "Unknown date"
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
}

function noopOpenArtifact() {
  return undefined
}

function noopCodePreview() {
  return undefined
}
