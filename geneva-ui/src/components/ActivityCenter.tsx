import { useEffect, useMemo, useState } from "react"
import { AlertTriangle, CheckCircle2, History, LockKeyhole, ShieldCheck, Sparkles, Wrench } from "lucide-react"

import { fetchSessionActivity } from "@/lib/api"
import type { SessionActivityItem, SkillMeta, ToolPermissionRequest } from "@/types"

export function ActivityCenter({
  pendingPermissionRequest,
  sessionId,
  skills,
}: {
  pendingPermissionRequest?: ToolPermissionRequest | null
  sessionId?: string | null
  skills: SkillMeta[]
}) {
  const [activities, setActivities] = useState<SessionActivityItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const activeSkills = useMemo(
    () =>
      [...skills]
        .filter((skill) => skill.status === "active")
        .sort((a, b) => (b.usage_count ?? 0) - (a.usage_count ?? 0))
        .slice(0, 4),
    [skills],
  )
  const permissionRisk = pendingPermissionRequest ? permissionRiskLabel(pendingPermissionRequest) : null

  useEffect(() => {
    if (!sessionId) {
      setActivities([])
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    void fetchSessionActivity(sessionId, 40)
      .then((payload) => {
        if (!cancelled) setActivities(payload.activities ?? [])
      })
      .catch((caught) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "Activity could not be loaded.")
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [sessionId])

  return (
    <section className="activity-center" aria-label="Activity and permissions">
      <div className="customize-heading">
        <p>Geneva</p>
        <h1>Activity & permissions</h1>
      </div>

      <div className="permission-center">
        <div className="permission-center-main">
          <span className="permission-center-icon">
            <ShieldCheck className="size-4" />
          </span>
          <div>
            <strong>{pendingPermissionRequest ? "Permission waiting" : "Balanced safety profile"}</strong>
            <p>
              {pendingPermissionRequest
                ? `${pendingPermissionRequest.toolName} needs a decision before Geneva continues.`
                : "Read-only context can run quietly; side effects ask before they happen."}
            </p>
          </div>
        </div>
        {pendingPermissionRequest ? (
          <div className="permission-center-request">
            <span className={`permission-center-risk risk-${permissionRisk?.level ?? "medium"}`}>
              {permissionRisk?.label ?? "Review"}
            </span>
            <span>{pendingPermissionRequest.message}</span>
          </div>
        ) : (
          <div className="permission-center-request muted">
            <LockKeyhole className="size-3.5" />
            <span>No pending approval in this chat.</span>
          </div>
        )}
      </div>

      <div className="activity-center-grid">
        <section className="activity-center-panel">
          <div className="activity-center-section-head">
            <History className="size-4" />
            <h2>Recent runs</h2>
            {loading ? <span>Loading</span> : null}
          </div>
          {!sessionId ? (
            <p className="activity-center-empty">Open or send a chat to see the audit trail here.</p>
          ) : error ? (
            <p className="activity-center-empty">{error}</p>
          ) : activities.length ? (
            <div className="activity-center-list">
              {activities.map((activity, index) => (
                <ActivityCenterRow activity={activity} key={`${activity.turn_id ?? "turn"}-${index}`} />
              ))}
            </div>
          ) : (
            <p className="activity-center-empty">No recorded tool or memory activity yet.</p>
          )}
        </section>

        <section className="activity-center-panel">
          <div className="activity-center-section-head">
            <Sparkles className="size-4" />
            <h2>Skill health</h2>
          </div>
          {activeSkills.length ? (
            <div className="skill-health-list">
              {activeSkills.map((skill) => (
                <div className="skill-health-row" key={skill.name}>
                  <span>/{skill.name}</span>
                  <strong>{skill.usage_count ?? 0} uses</strong>
                  <small>{skill.safety_status ? skillSafetyLabel(skill.safety_status) : "Safety passed"}</small>
                </div>
              ))}
            </div>
          ) : (
            <p className="activity-center-empty">Activate a skill to see its recent use here.</p>
          )}
        </section>
      </div>
    </section>
  )
}

function ActivityCenterRow({ activity }: { activity: SessionActivityItem }) {
  const toolNames = (activity.tool_names ?? []).filter(Boolean)
  const hasError = (activity.error_count ?? 0) > 0
  return (
    <article className={`activity-center-row ${hasError ? "has-error" : ""}`}>
      <span className="activity-center-row-icon">
        {hasError ? <AlertTriangle className="size-3.5" /> : toolNames.length ? <Wrench className="size-3.5" /> : <CheckCircle2 className="size-3.5" />}
      </span>
      <div>
        <strong>{activity.user_preview || "Assistant run"}</strong>
        <p>
          {toolNames.length ? `Tools: ${toolNames.map(formatToolName).join(", ")}` : "No tool calls"}
          {activity.memory_action ? ` · Memory ${activity.memory_action}` : ""}
          {hasError ? ` · ${activity.error_count} issue${activity.error_count === 1 ? "" : "s"}` : ""}
        </p>
      </div>
      <time>{formatActivityTime(activity.created_at)}</time>
    </article>
  )
}

function permissionRiskLabel(request: ToolPermissionRequest): { level: "low" | "medium" | "high"; label: string } {
  const text = `${request.toolName} ${request.message} ${request.suggestion ?? ""}`.toLowerCase()
  if (/delete|destructive|write|edit|shell|bash|terminal|network|computer/.test(text)) {
    return { level: "high", label: "Higher risk" }
  }
  if (/file|source|connect|token|secret|permission/.test(text)) {
    return { level: "medium", label: "Review access" }
  }
  return { level: "low", label: "Low risk" }
}

function skillSafetyLabel(status: string): string {
  if (status === "blocked") return "Blocked"
  if (status === "warning") return "Needs review"
  return "Safety passed"
}

function formatToolName(name: string): string {
  return name
    .replace(/Tool$/, "")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .trim()
}

function formatActivityTime(value?: string | null): string {
  if (!value) return ""
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ""
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
}
