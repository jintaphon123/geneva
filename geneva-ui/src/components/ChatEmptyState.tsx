import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { Ghost } from "lucide-react"

import { GenevaMark } from "@/components/GenevaMark"
import type { MemoryStats } from "@/types"

export function EmptyState({
  ghostMode,
}: {
  ghostMode: boolean
  memoryStats: MemoryStats
}) {
  const [greeting, setGreeting] = useState(() => getTimeGreeting())

  useEffect(() => {
    const timer = window.setInterval(() => setGreeting(getTimeGreeting()), 60000)
    return () => window.clearInterval(timer)
  }, [])

  return (
    <div className="empty-state">
      <motion.div
        animate={{ opacity: 1, y: 0 }}
        className="empty-mark"
        initial={{ opacity: 0, y: 8 }}
        transition={{ duration: 0.24, ease: "easeOut" }}
      >
        <GenevaMark />
      </motion.div>
      <motion.h1
        animate={{ opacity: 1, y: 0 }}
        initial={{ opacity: 0, y: 10 }}
        transition={{ delay: 0.04, duration: 0.26, ease: "easeOut" }}
      >
        {greeting}
      </motion.h1>
      {ghostMode ? (
        <motion.div
          animate={{ opacity: 1, y: 0 }}
          className="memory-chip ghost-chip"
          initial={{ opacity: 0, y: 10 }}
          transition={{ delay: 0.08, duration: 0.26, ease: "easeOut" }}
        >
          <Ghost className="size-3.5" />
          Incognito chat
        </motion.div>
      ) : null}
    </div>
  )
}

function getTimeGreeting(): string {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 8) return "Gentle morning. Geneva is ready"
  if (hour >= 8 && hour < 11) return "Good morning. Geneva is ready"
  if (hour >= 11 && hour < 12) return "Gather your thoughts with Geneva"
  if (hour >= 12 && hour < 13) return "Midday reset with Geneva"
  if (hour >= 13 && hour < 17) return "Good afternoon. What are we building?"
  if (hour >= 17 && hour < 19) return "Golden hour. Let's make it count"
  if (hour >= 19 && hour < 22) return "Good evening. Geneva is here"
  if (hour >= 22 || hour < 1) return "Late-night session. Geneva is still here"
  return "Geneva is ready"
}
