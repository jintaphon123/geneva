import { AlertTriangle, History, LockKeyhole, ShieldCheck } from "lucide-react"

import type { ToolPermissionRequest } from "@/types"

export function ToolPermissionModal({
  onResolve,
  request,
}: {
  onResolve: (approved: boolean) => void
  request: ToolPermissionRequest
}) {
  const risk = permissionRiskLabel(request)
  const RiskIcon = risk.icon
  return (
    <div className="tool-permission-backdrop">
      <section aria-label="Tool permission request" className="tool-permission-panel">
        <div className="tool-permission-icon">
          <LockKeyhole className="size-4" />
        </div>
        <div className="tool-permission-copy">
          <span className="tool-permission-kicker">Tool permission</span>
          <h2>{request.toolName}</h2>
          <div className={`tool-permission-risk risk-${risk.level}`}>
            <RiskIcon className="size-3.5" />
            <span>{risk.label}</span>
          </div>
          <div className="tool-permission-detail-grid">
            <div>
              <strong>What it wants</strong>
              <p>{request.message}</p>
            </div>
            <div>
              <strong>Why this appears</strong>
              <p>{request.suggestion || "This action can affect files, tools, connectors, or external state."}</p>
            </div>
            <div>
              <strong>Audit trail</strong>
              <p>This decision is attached to the current run and appears in Activity.</p>
            </div>
          </div>
          <span className="tool-permission-timeout">
            Auto-denies after {Math.round(request.timeoutSeconds)}s without approval
          </span>
        </div>
        <div className="tool-permission-actions">
          <button className="tool-permission-deny" onClick={() => onResolve(false)} type="button">
            Deny
          </button>
          <button className="tool-permission-approve" onClick={() => onResolve(true)} type="button">
            Approve once
          </button>
        </div>
      </section>
    </div>
  )
}

function permissionRiskLabel(request: ToolPermissionRequest): {
  icon: typeof AlertTriangle
  label: string
  level: "low" | "medium" | "high"
} {
  const text = `${request.toolName} ${request.message} ${request.suggestion ?? ""}`.toLowerCase()
  if (/delete|destructive|write|edit|shell|bash|terminal|computer|network|external/.test(text)) {
    return { icon: AlertTriangle, label: "Higher risk action", level: "high" }
  }
  if (/file|source|connector|secret|token|permission/.test(text)) {
    return { icon: History, label: "Review access", level: "medium" }
  }
  return { icon: ShieldCheck, label: "Low risk action", level: "low" }
}
