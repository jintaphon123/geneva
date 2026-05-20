import { useEffect, useState } from "react"
import { Check, Pencil, Telescope, X } from "lucide-react"

export type ResearchPlanCardProps = {
  title: string
  steps: string[]
  onStart: (title: string, steps: string[]) => void
  onCancel: () => void
}

function parseSteps(raw: string): string[] {
  return raw
    .split(/\r?\n/)
    .map((value) => value.trim())
    .filter((value) => value.length > 0)
}

export function ResearchPlanCard({
  title,
  steps,
  onStart,
  onCancel,
}: ResearchPlanCardProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [draftSteps, setDraftSteps] = useState(steps.join("\n"))
  const [currentSteps, setCurrentSteps] = useState<string[]>(steps)

  useEffect(() => {
    setCurrentSteps(steps)
    setDraftSteps(steps.join("\n"))
  }, [steps])

  function handleSavePlan() {
    const nextSteps = parseSteps(draftSteps)
    setCurrentSteps(nextSteps.length ? nextSteps : currentSteps)
    setIsEditing(false)
  }

  function handleStart() {
    onStart(title, currentSteps)
  }

  return (
    <div className="research-plan-card">
      <div className="research-plan-header">
        <span className="research-plan-icon">
          <Telescope className="size-4" />
        </span>
        <div>
          <span>Deep Research</span>
          <h2>Review plan</h2>
          <p>{title}</p>
        </div>
      </div>

      {isEditing ? (
        <div className="research-plan-editor">
          <textarea
            className="research-plan-card-editor"
            onChange={(event) => setDraftSteps(event.currentTarget.value)}
            rows={Math.max(5, currentSteps.length + 1)}
            value={draftSteps}
          />
          <div className="research-plan-actions">
            <button className="research-plan-secondary" onClick={() => setIsEditing(false)} type="button">
              <X className="size-3.5" />
              Cancel edit
            </button>
            <button className="research-plan-primary" onClick={handleSavePlan} type="button">
              <Check className="size-3.5" />
              Save plan
            </button>
          </div>
        </div>
      ) : (
        <>
          <ol className="research-plan-steps">
            {currentSteps.map((step, index) => (
              <li className="research-plan-step" key={`${step}-${index}`}>
                <span>{index + 1}</span>
                <p>{step}</p>
              </li>
            ))}
          </ol>
          <div className="research-plan-note">
            Geneva will turn this into a durable research report with sources and a saved artifact.
          </div>
          <div className="research-plan-actions">
            <button className="research-plan-secondary" onClick={() => setIsEditing(true)} type="button">
              <Pencil className="size-3.5" />
              Edit plan
            </button>
            <button className="research-plan-secondary" onClick={onCancel} type="button">
              <X className="size-3.5" />
              Cancel
            </button>
            <button className="research-plan-primary" onClick={handleStart} type="button">
              <Telescope className="size-3.5" />
              Start research
            </button>
          </div>
        </>
      )}
    </div>
  )
}
