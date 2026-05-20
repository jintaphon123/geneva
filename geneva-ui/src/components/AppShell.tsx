import { type MouseEvent, type ReactNode, useEffect, useState } from "react"
import { motion } from "framer-motion"
import { Menu, X } from "lucide-react"

import { cn } from "@/lib/utils"

type AppShellProps = {
  sidebar: ReactNode
  children: ReactNode
  memoryPanel: ReactNode
  memoryOpen: boolean
  sidebarCollapsed: boolean
  skillMode?: boolean
}

export function AppShell({ sidebar, children, memoryPanel, memoryOpen, sidebarCollapsed, skillMode }: AppShellProps) {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)

  useEffect(() => {
    if (!mobileSidebarOpen) return
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setMobileSidebarOpen(false)
    }
    document.addEventListener("keydown", closeOnEscape)
    return () => document.removeEventListener("keydown", closeOnEscape)
  }, [mobileSidebarOpen])

  function handleSidebarClick(event: MouseEvent<HTMLElement>) {
    if (!mobileSidebarOpen) return
    const target = event.target
    if (!(target instanceof HTMLElement)) return
    if (target.closest("button")) setMobileSidebarOpen(false)
  }

  return (
    <div
      className={cn(
        "app-shell",
        !memoryOpen && "memory-closed",
        sidebarCollapsed && "sidebar-collapsed",
        skillMode && "skill-mode",
        mobileSidebarOpen && "mobile-nav-open",
      )}
    >
      <button
        aria-label={mobileSidebarOpen ? "Close navigation" : "Open navigation"}
        className="mobile-sidebar-trigger"
        onClick={() => setMobileSidebarOpen((open) => !open)}
        type="button"
      >
        {mobileSidebarOpen ? <X className="size-4" /> : <Menu className="size-4" />}
      </button>
      {mobileSidebarOpen ? (
        <button
          aria-label="Close navigation overlay"
          className="mobile-sidebar-backdrop"
          onClick={() => setMobileSidebarOpen(false)}
          type="button"
        />
      ) : null}
      <aside className={cn("app-sidebar", mobileSidebarOpen && "mobile-open")} onClickCapture={handleSidebarClick}>
        {sidebar}
      </aside>
      <main className="app-main">{children}</main>
      <motion.aside
        animate={{ opacity: memoryOpen ? 1 : 0, x: memoryOpen ? 0 : 18 }}
        className="app-memory"
        initial={false}
        transition={{ duration: 0.18, ease: "easeOut" }}
      >
        {memoryOpen ? memoryPanel : null}
      </motion.aside>
    </div>
  )
}
