import { motion } from "framer-motion"

import { GenevaMark, type GenevaMarkState } from "@/components/GenevaMark"

export function StatusLine({ text }: { text: string }) {
  return (
    <motion.div
      animate={{ opacity: 1, y: 0 }}
      className="status-line"
      initial={{ opacity: 0, y: 6 }}
      transition={{ duration: 0.16 }}
    >
      <GenevaMark className="status-mark status-guide-mark" state={statusMarkState(text)} variant="loader" />
      {text}
    </motion.div>
  )
}

function statusMarkState(text: string): GenevaMarkState {
  const normalized = text.toLowerCase()
  if (normalized.includes("thinking") || normalized.includes("searching") || normalized.includes("reading")) {
    return "thinking"
  }
  if (normalized.includes("planning") || normalized.includes("ready") || normalized.includes("finished")) {
    return "merging"
  }
  if (normalized.includes("failed") || normalized.includes("timeout")) return "error"
  return "responding"
}
