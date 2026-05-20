import { useEffect } from "react"
import { BookOpenCheck, Braces, LockKeyhole, Network, PackageOpen, Sparkles, X } from "lucide-react"

export function OpenSourceModal({ onClose }: { onClose: () => void }) {
  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") onClose()
    }
    document.addEventListener("keydown", closeOnEscape)
    return () => document.removeEventListener("keydown", closeOnEscape)
  }, [onClose])

  return (
    <div className="open-source-backdrop" role="presentation">
      <section aria-label="Library" aria-modal="true" className="open-source-panel" role="dialog">
        <button aria-label="Close Library" className="open-source-close" onClick={onClose} type="button">
          <X className="size-4" />
        </button>
        <div className="open-source-topline">
          <div className="open-source-kicker">
            <PackageOpen className="size-4" />
            Library Control Plane
          </div>
          <span>Private-first reuse registry</span>
        </div>
        <h2>Reusable Intelligence Library</h2>
        <p>
          Generated code, simulations, prompts, and project artifacts become reusable building blocks.
          Future agents should adapt what already exists before spending tokens rebuilding the same thing.
        </p>
        <div className="open-source-metrics" aria-label="Library readiness">
          <div className="open-source-metric">
            <span>Registry</span>
            <strong>Local-first</strong>
          </div>
          <div className="open-source-metric">
            <span>Review gate</span>
            <strong>Required</strong>
          </div>
          <div className="open-source-metric">
            <span>Reuse policy</span>
            <strong>Search first</strong>
          </div>
          <div className="open-source-metric">
            <span>Default scope</span>
            <strong>Private</strong>
          </div>
        </div>
        <div className="open-source-flow" aria-label="Library pipeline">
          <div>
            <span>01</span>
            Generate
          </div>
          <div>
            <span>02</span>
            Review
          </div>
          <div>
            <span>03</span>
            Publish
          </div>
          <div>
            <span>04</span>
            Reuse
          </div>
        </div>
        <div className="open-source-sections">
          <div className="open-source-grid">
            <div>
              <Braces className="size-5" />
              <span>Reusable assets</span>
              <p>Thermo simulations and reusable learning tools for everyone.</p>
            </div>
            <div>
              <BookOpenCheck className="size-5" />
              <span>Review queue</span>
              <p>Generated artifacts must pass quality gates before becoming trusted source.</p>
            </div>
            <div>
              <PackageOpen className="size-5" />
              <span>Reuse index</span>
              <p>Agents search existing code first, then adapt the closest match.</p>
            </div>
            <div>
              <Network className="size-5" />
              <span>Team libraries</span>
              <p>Org-specific code and references stay inside the school or company.</p>
            </div>
            <div>
              <LockKeyhole className="size-5" />
              <span>Private work</span>
              <p>Personal generated code remains scoped to the owner by default.</p>
            </div>
            <div>
              <Sparkles className="size-5" />
              <span>Agent memory</span>
              <p>Published assets become context candidates for future project chats.</p>
            </div>
          </div>
          <div className="open-source-governance">
            <h3>Publish contract</h3>
            <p>Nothing becomes reusable source until it has provenance, license intent, quality notes, and a private/public scope.</p>
            <div>
              <span>Required metadata</span>
              <strong>owner, source session, review status, reuse tags</strong>
            </div>
            <div>
              <span>Agent behavior</span>
              <strong>search registry before generating similar work</strong>
            </div>
          </div>
        </div>
        <div className="open-source-footer">
          <span>Next build: registry-backed publish queue with project-scoped visibility.</span>
          <button onClick={onClose} type="button">Back to workspace</button>
        </div>
      </section>
    </div>
  )
}
