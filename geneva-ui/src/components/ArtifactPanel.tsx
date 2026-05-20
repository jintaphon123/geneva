import { useEffect, useMemo, useState } from "react"
import { motion } from "framer-motion"
import { Check, Copy, X } from "lucide-react"

export type Artifact = {
  language: string
  code: string
  title: string
}

interface ArtifactPanelProps {
  artifact: Artifact | null
  onClose: () => void
}

export function ArtifactPanel({ artifact, onClose }: ArtifactPanelProps) {
  const [renderedArtifact, setRenderedArtifact] = useState<Artifact | null>(artifact)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (artifact) setRenderedArtifact(artifact)
  }, [artifact])

  useEffect(() => {
    setCopied(false)
  }, [artifact?.code])

  const visibleArtifact = artifact ?? renderedArtifact
  const language = visibleArtifact?.language.toLowerCase() || "text"
  const sanitizedSvg = useMemo(
    () => (language === "svg" && visibleArtifact ? sanitizeSvg(visibleArtifact.code) : ""),
    [language, visibleArtifact],
  )

  function handleCopy() {
    if (!visibleArtifact?.code) return
    void navigator.clipboard
      .writeText(visibleArtifact.code)
      .then(() => {
        setCopied(true)
        window.setTimeout(() => setCopied(false), 1500)
      })
      .catch(() => undefined)
  }

  return (
    <motion.aside
      aria-hidden={!artifact}
      animate={{ x: artifact ? 0 : 380, width: artifact ? 380 : 0 }}
      className="artifact-panel"
      initial={false}
      onAnimationComplete={() => {
        if (!artifact) setRenderedArtifact(null)
      }}
      transition={{ duration: 0.22, ease: "easeOut" }}
    >
      {visibleArtifact ? (
        <>
          <header className="artifact-panel-header">
            <span className="artifact-lang-badge">{language}</span>
            <h2 className="artifact-panel-title">{visibleArtifact.title}</h2>
            <button
              aria-label={copied ? "Copied artifact code" : "Copy artifact code"}
              className="artifact-panel-icon-button"
              onClick={handleCopy}
              title={copied ? "Copied" : "Copy"}
              type="button"
            >
              {copied ? <Check className="size-4 text-emerald-500" /> : <Copy className="size-4" />}
            </button>
            <button
              aria-label="Close artifact panel"
              className="artifact-panel-icon-button"
              onClick={onClose}
              title="Close"
              type="button"
            >
              <X className="size-4" />
            </button>
          </header>
          <div className="artifact-panel-body">
            {language === "html" ? (
              <iframe
                className="artifact-html-frame"
                sandbox=""
                srcDoc={visibleArtifact.code}
                title={visibleArtifact.title}
              />
            ) : language === "svg" ? (
              <img
                alt={visibleArtifact.title || "SVG artifact"}
                className="artifact-svg-preview"
                src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(sanitizedSvg)}`}
              />
            ) : (
              <pre className="artifact-code-block">
                <code className={`language-${language}`}>{visibleArtifact.code}</code>
              </pre>
            )}
          </div>
        </>
      ) : null}
    </motion.aside>
  )
}

function sanitizeSvg(svg: string): string {
  return svg
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "")
    .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, "")
    .replace(/\s+on[a-z]+\s*=\s*(".*?"|'.*?'|[^\s>]+)/gi, "")
    .replace(/\s+(href|xlink:href)\s*=\s*(["'])\s*javascript:[\s\S]*?\2/gi, "")
}
