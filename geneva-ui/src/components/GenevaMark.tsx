import { cn } from "@/lib/utils"

export type GenevaMarkState = "idle" | "thinking" | "merging" | "responding" | "paused" | "error"
type GenevaMarkVariant = "dot" | "mark" | "blob" | "loader"

type GenevaMarkProps = {
  className?: string
  state?: GenevaMarkState
  variant?: GenevaMarkVariant
}

export function GenevaMark({
  className,
  state = "idle",
  variant = "mark",
}: GenevaMarkProps) {
  if (variant === "dot") {
    return (
      <span
        aria-hidden="true"
        className={cn("geneva-mark geneva-mark-dot", `geneva-mark-${state}`, className)}
      />
    )
  }

  if (variant === "loader") {
    return (
      <span
        aria-hidden="true"
        className={cn(
          "geneva-mark geneva-mark-loader",
          `geneva-mark-${state}`,
          `geneva-mark-loader-${state}`,
          className,
        )}
      >
        <span className="geneva-mark-loader-line" />
        <span className="geneva-mark-loader-large" />
        <span className="geneva-mark-loader-small" />
      </span>
    )
  }

  if (variant === "blob" || state === "responding") {
    return (
      <span
        aria-hidden="true"
        className={cn("geneva-mark geneva-mark-blob", `geneva-mark-${state}`, className)}
      />
    )
  }

  return (
    <svg
      aria-hidden="true"
      className={cn("geneva-mark geneva-mark-svg", `geneva-mark-${state}`, className)}
      fill="none"
      viewBox="0 0 110 28"
    >
      <line
        className="geneva-mark-line"
        strokeLinecap="round"
        strokeWidth="2.5"
        x1="23"
        x2="88"
        y1="14"
        y2="14"
      />
      <circle className="geneva-mark-node geneva-mark-node-large" cx="11" cy="14" r="11" />
      <circle className="geneva-mark-node geneva-mark-node-small" cx="98" cy="14" r="8" />
    </svg>
  )
}
