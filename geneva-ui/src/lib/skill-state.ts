import type { SkillMeta } from "@/types"

export function hasPassedEval(skill: SkillMeta | null): boolean {
  return Boolean(skill?.eval_cases?.some((item) => item.status === "passed"))
}

export function needsEvalBeforeActivation(skill: SkillMeta | null): boolean {
  return Boolean(skill && (skill.source === "generated" || skill.source === "feedback"))
}

export function canActivateSkill(skill: SkillMeta): boolean {
  if (skill.safety_status === "blocked") return false
  return !needsEvalBeforeActivation(skill) || hasPassedEval(skill)
}

export function passedEvalCount(skill: SkillMeta): number {
  return skill.eval_cases?.filter((item) => item.status === "passed").length ?? 0
}

export function skillDisplaySource(skill: SkillMeta): string {
  if (skill.source === "feedback") return "feedback"
  if (skill.source === "generated") return "generated"
  if (skill.source === "managed") return "managed"
  return skill.source || "local"
}

export function activationBlockedReason(skill: SkillMeta): string | null {
  if (skill.safety_status === "blocked") return `/${skill.name} is blocked by the safety scan. Open Details and fix the findings first.`
  if (needsEvalBeforeActivation(skill) && !hasPassedEval(skill)) {
    return `/${skill.name} needs one passed rehearsal before activation.`
  }
  return null
}

export function skillReadinessTone(skill: SkillMeta): "ready" | "review" | "blocked" | "neutral" {
  if (skill.safety_status === "blocked" || skill.safety_status === "warning") return "blocked"
  if (skill.status === "active") return "ready"
  if (activationBlockedReason(skill)) return "review"
  if (canActivateSkill(skill)) return "ready"
  return "neutral"
}

export function skillReadinessLabel(skill: SkillMeta): string {
  if (skill.status === "active") return "live in chat"
  if (skill.safety_status === "blocked") return "safety blocked"
  if (skill.safety_status === "warning") return "safety review"
  if (needsEvalBeforeActivation(skill) && !hasPassedEval(skill)) return "needs rehearsal"
  if (canActivateSkill(skill)) return "ready to activate"
  return "inactive"
}

export function skillErrorMessage(error: unknown, fallback: string): string {
  const raw = error instanceof Error ? error.message : String(error || "")
  if (/network|fetch|connection|timeout|timed out/i.test(raw)) {
    return "Skill control plane lost the local server connection. Existing skills remain visible; retry when the server is reachable."
  }
  if (/404|not found/i.test(raw)) return "That skill no longer exists in the control plane. Refresh the list before continuing."
  if (/blocked|safety|rehearsal|eval/i.test(raw)) return raw
  return fallback
}
