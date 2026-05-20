import { useEffect, useState } from "react"
import { AlertTriangle, CheckCircle2, Plus, RefreshCcw, Sparkles, Wand2, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { activateSkill, addSkillEval, buildSkill, fetchSkill, rollbackSkill, submitSkillFeedback, updateSkill } from "@/lib/api"
import { cn } from "@/lib/utils"
import { canActivateSkill, hasPassedEval, needsEvalBeforeActivation, skillErrorMessage } from "@/lib/skill-state"
import type { SkillMeta } from "@/types"

export function SkillDetailModal({ name, onClose }: { name: string; onClose: () => void }) {
  const [skill, setSkill] = useState<(SkillMeta & { system_prompt: string }) | null>(null)
  const [evalInput, setEvalInput] = useState("")
  const [evalExpected, setEvalExpected] = useState("")
  const [feedbackOutcome, setFeedbackOutcome] = useState("")
  const [feedbackChange, setFeedbackChange] = useState("")
  const [feedbackScore, setFeedbackScore] = useState(3)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    void fetchSkill(name)
      .then((result) => {
        setSkill(result.skill)
        setError(null)
      })
      .catch((caught) => setError(skillErrorMessage(caught, `Could not load /${name}.`)))
  }, [name])

  async function handleAddEval() {
    if (!skill || !evalInput.trim() || !evalExpected.trim()) return
    setSaving(true)
    setError(null)
    try {
      const result = await addSkillEval(
        skill.name,
        evalInput.trim(),
        evalExpected.trim(),
        "passed",
        "Manual rehearsal passed.",
        "Reviewed from Skill Control Plane.",
      )
      setSkill({ ...(result.skill as SkillMeta & { system_prompt: string }), system_prompt: skill.system_prompt })
      setEvalInput("")
      setEvalExpected("")
    } catch (caught) {
      setError(skillErrorMessage(caught, "Could not record this rehearsal."))
    } finally {
      setSaving(false)
    }
  }

  async function handleRollback(revisionId: string) {
    if (!skill) return
    setSaving(true)
    setError(null)
    try {
      const result = await rollbackSkill(skill.name, revisionId)
      setSkill(result.skill as SkillMeta & { system_prompt: string })
    } catch (caught) {
      setError(skillErrorMessage(caught, "Could not rollback this skill revision."))
    } finally {
      setSaving(false)
    }
  }

  async function handleFeedback() {
    if (!skill || !feedbackOutcome.trim()) return
    setSaving(true)
    setError(null)
    try {
      const result = await submitSkillFeedback(
        skill.name,
        feedbackScore,
        feedbackOutcome.trim(),
        "",
        feedbackChange.trim(),
      )
      setSkill(result.skill as SkillMeta & { system_prompt: string })
      setFeedbackOutcome("")
      setFeedbackChange("")
      setFeedbackScore(3)
    } catch (caught) {
      setError(skillErrorMessage(caught, "Could not save skill feedback."))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="skill-modal-backdrop">
      <div className="skill-modal">
        <button className="skill-modal-close" onClick={onClose} type="button">
          <X className="size-4" />
        </button>
        <h3>{skill?.name ?? name}</h3>
        <p className="skill-modal-desc">{skill?.description ?? "Loading..."}</p>
        {error ? (
          <div className="skill-notice error" role="alert">
            <AlertTriangle className="size-4" />
            <span>{error}</span>
            <button onClick={() => setError(null)} type="button">
              Dismiss
            </button>
          </div>
        ) : null}
        <div className="skill-detail-badges">
          <span className={cn("skill-status-pill", skill?.status)}>{skill?.status ?? "loading"}</span>
          <span className={cn("skill-safety-pill", skill?.safety_status)}>
            {skill?.safety_status ?? "unknown"}
          </span>
          <span>{skill?.source ?? "source unknown"}</span>
        </div>
        <div className="skill-detail-row">
          <span>Command</span>
          <code>{skill?.command ?? `/${name}`}</code>
        </div>
        <div className="skill-detail-row">
          <span>Triggers</span>
          <p>{skill?.triggers?.join(", ") || "Loading..."}</p>
        </div>
        <div className="skill-detail-row">
          <span>Usage</span>
          <p>{skill ? `${skill.usage_count ?? 0} runs` : "Loading..."}</p>
        </div>
        {skill?.generated_from ? (
          <div className="skill-detail-row">
            <span>Provenance</span>
            <p>{skill.generated_from}</p>
          </div>
        ) : null}
        {skill?.safety_findings?.length ? (
          <div className="skill-safety-list">
            {skill.safety_findings.map((finding) => (
              <span key={finding}>{finding}</span>
            ))}
          </div>
        ) : null}
        <div className="skill-quality-panel">
          <div className="skill-quality-header">
            <span>Quality gate</span>
            <strong>{hasPassedEval(skill) ? "ready" : needsEvalBeforeActivation(skill) ? "needs rehearsal" : "optional"}</strong>
          </div>
          <div className="skill-eval-list">
            {(skill?.eval_cases ?? []).length === 0 ? (
              <p>No rehearsal cases yet.</p>
            ) : (
              skill?.eval_cases?.map((item) => (
                <div className="skill-eval-item" key={item.id}>
                  <span className={cn("skill-status-pill", item.status)}>{item.status}</span>
                  <p>{item.input}</p>
                  <small>{item.expected}</small>
                </div>
              ))
            )}
          </div>
          <div className="skill-inline-form">
            <input
              onChange={(event) => setEvalInput(event.target.value)}
              placeholder="Sample input"
              value={evalInput}
            />
            <input
              onChange={(event) => setEvalExpected(event.target.value)}
              placeholder="Expected behavior"
              value={evalExpected}
            />
            <Button
              disabled={saving || !evalInput.trim() || !evalExpected.trim()}
              onClick={() => void handleAddEval()}
              type="button"
              variant="subtle"
            >
              <CheckCircle2 className="size-4" />
              Record pass
            </Button>
          </div>
        </div>
        <div className="skill-quality-panel">
          <div className="skill-quality-header">
            <span>Feedback loop</span>
            <strong>{skill?.feedback_summary?.average_score ?? "no score"}</strong>
          </div>
          <div className="skill-inline-form">
            <input
              max={5}
              min={1}
              onChange={(event) => setFeedbackScore(Number(event.target.value))}
              type="number"
              value={feedbackScore}
            />
            <input
              onChange={(event) => setFeedbackOutcome(event.target.value)}
              placeholder="Outcome"
              value={feedbackOutcome}
            />
            <input
              onChange={(event) => setFeedbackChange(event.target.value)}
              placeholder="Suggested change"
              value={feedbackChange}
            />
            <Button
              disabled={saving || !feedbackOutcome.trim()}
              onClick={() => void handleFeedback()}
              type="button"
              variant="subtle"
            >
              <Sparkles className="size-4" />
              Save feedback
            </Button>
          </div>
        </div>
        {skill?.revisions?.length ? (
          <div className="skill-quality-panel">
            <div className="skill-quality-header">
              <span>Revisions</span>
              <strong>{skill.revisions.length}</strong>
            </div>
            <div className="skill-revision-list">
              {skill.revisions.slice(-5).map((revision) => (
                <button
                  disabled={saving}
                  key={revision.id}
                  onClick={() => void handleRollback(revision.id)}
                  type="button"
                >
                  <RefreshCcw className="size-3.5" />
                  <span>{revision.note || revision.source}</span>
                  <small>{revision.created_at}</small>
                </button>
              ))}
            </div>
          </div>
        ) : null}
        <textarea
          className="skill-generated-preview"
          readOnly
          rows={8}
          value={skill?.system_prompt ?? ""}
        />
      </div>
    </div>
  )
}

export function BuildSkillModal({
  onClose,
  onGenerated,
  onSaved,
}: {
  onClose: () => void
  onGenerated: () => void
  onSaved: () => void
}) {
  const [description, setDescription] = useState("")
  const [raw, setRaw] = useState("")
  const [generating, setGenerating] = useState(false)
  const [editing, setEditing] = useState(false)
  const [savingEdits, setSavingEdits] = useState(false)
  const [activating, setActivating] = useState(false)
  const [created, setCreated] = useState<SkillMeta | null>(null)
  const [evalInput, setEvalInput] = useState("")
  const [evalExpected, setEvalExpected] = useState("")
  const [error, setError] = useState<string | null>(null)

  async function handleGenerate() {
    if (!description.trim()) return
    setGenerating(true)
    setError(null)
    try {
      const result = await buildSkill(description.trim())
      setCreated(result.skill)
      setRaw(result.raw)
      onGenerated()
    } catch (caught) {
      setError(skillErrorMessage(caught, "Could not generate a review draft. Tighten the description, then retry."))
    } finally {
      setGenerating(false)
    }
  }

  async function handleDone() {
    setError(null)
    if (created && editing) {
      setSavingEdits(true)
      try {
        await updateSkill(created.name, raw)
      } catch (caught) {
        setError(skillErrorMessage(caught, "Could not save skill edits."))
        return
      } finally {
        setSavingEdits(false)
      }
    }
    onSaved()
  }

  async function handleActivate() {
    if (!created) return
    setError(null)
    if (editing) {
      setSavingEdits(true)
      try {
        await updateSkill(created.name, raw)
      } catch (caught) {
        setError(skillErrorMessage(caught, "Could not save skill edits before activation."))
        return
      } finally {
        setSavingEdits(false)
      }
    }
    setActivating(true)
    try {
      await activateSkill(created.name)
      onSaved()
    } catch (caught) {
      setError(skillErrorMessage(caught, `Could not activate /${created.name}.`))
    } finally {
      setActivating(false)
    }
  }

  async function handleRecordEval() {
    if (!created || !evalInput.trim() || !evalExpected.trim()) return
    setSavingEdits(true)
    setError(null)
    try {
      const result = await addSkillEval(
        created.name,
        evalInput.trim(),
        evalExpected.trim(),
        "passed",
        "Manual rehearsal passed.",
        "Reviewed before activation.",
      )
      setCreated(result.skill)
      setEvalInput("")
      setEvalExpected("")
      onGenerated()
    } catch (caught) {
      setError(skillErrorMessage(caught, "Could not record this rehearsal pass."))
    } finally {
      setSavingEdits(false)
    }
  }

  return (
    <div className="skill-modal-backdrop">
      <div className={cn("skill-modal", "wide")}>
        <button className="skill-modal-close" onClick={onClose} type="button">
          <X className="size-4" />
        </button>
        <h3>Build new skill</h3>
        <label className="skill-modal-label" htmlFor="skill-description">
          Describe the skill you want
        </label>
        <textarea
          className="skill-builder-input"
          id="skill-description"
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Example: A launch planning skill that stress-tests messaging, channels, timing, and risks"
          rows={5}
          value={description}
        />
        {error ? (
          <div className="skill-notice error" role="alert">
            <AlertTriangle className="size-4" />
            <span>{error}</span>
            <button onClick={() => setError(null)} type="button">
              Dismiss
            </button>
          </div>
        ) : null}
        <div className="skill-modal-actions">
          <Button disabled={generating || !description.trim()} onClick={handleGenerate} type="button">
            <Wand2 className="size-4" />
            {generating ? "Generating..." : "Generate review draft"}
          </Button>
          {created ? (
            <Button onClick={() => setEditing((value) => !value)} type="button" variant="subtle">
              <Plus className="size-4" />
              {editing ? "Preview" : "Edit"}
            </Button>
          ) : null}
          {created ? (
            <Button
              disabled={activating || !canActivateSkill(created)}
              onClick={() => void handleActivate()}
              type="button"
              variant="subtle"
            >
              <CheckCircle2 className="size-4" />
              {activating ? "Activating..." : "Activate"}
            </Button>
          ) : null}
          {created ? (
            <Button disabled={savingEdits} onClick={() => void handleDone()} type="button" variant="subtle">
              <Plus className="size-4" />
              {savingEdits ? "Saving..." : "Keep in review"}
            </Button>
          ) : null}
        </div>
        {created ? (
          <p className="saved-badge">
            Generated /{created.name} · {created.status} · {created.safety_status}
          </p>
        ) : null}
        {created && needsEvalBeforeActivation(created) && !hasPassedEval(created) ? (
          <div className="skill-quality-panel builder">
            <div className="skill-quality-header">
              <span>Activation requires one passed rehearsal</span>
              <strong>blocked</strong>
            </div>
            <div className="skill-inline-form">
              <input
                onChange={(event) => setEvalInput(event.target.value)}
                placeholder="Sample input"
                value={evalInput}
              />
              <input
                onChange={(event) => setEvalExpected(event.target.value)}
                placeholder="Expected behavior"
                value={evalExpected}
              />
              <Button
                disabled={savingEdits || !evalInput.trim() || !evalExpected.trim()}
                onClick={() => void handleRecordEval()}
                type="button"
                variant="subtle"
              >
                <CheckCircle2 className="size-4" />
                Record rehearsal pass
              </Button>
            </div>
          </div>
        ) : null}
        {raw ? (
          <textarea
            className="skill-generated-preview"
            onChange={(event) => setRaw(event.target.value)}
            readOnly={!editing}
            rows={12}
            value={raw}
          />
        ) : null}
      </div>
    </div>
  )
}
