import { useMemo, useState } from "react"
import {
  ArrowLeft,
  Brain,
  Cable,
  ChevronRight,
  CircleGauge,
  History,
  MessageSquareText,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react"

import { ActivityCenter } from "@/components/ActivityCenter"
import { ConnectorsManager } from "@/components/ConnectorsManager"
import { MemoryBrowser } from "@/components/MemoryBrowser"
import { SkillBrowser } from "@/components/SkillBrowser"
import type { SkillMeta, ToolPermissionRequest } from "@/types"
import { cn } from "@/lib/utils"

type CustomizeView = "overview" | "personalization" | "skills" | "memory" | "connectors" | "activity"

type CustomizeSurfaceProps = {
  currentSessionId?: string | null
  onBack: () => void
  onCreateSkillChat?: () => void
  onSelectSkill: (trigger: string) => void
  onSkillsChanged?: (skills: SkillMeta[]) => void
  pendingPermissionRequest?: ToolPermissionRequest | null
  skills?: SkillMeta[]
}

const CUSTOMIZE_NAV: Array<{
  id: CustomizeView
  label: string
  detail: string
  icon: typeof Sparkles
}> = [
  {
    id: "personalization",
    label: "Personalization",
    detail: "Style, owner context, and response preferences",
    icon: SlidersHorizontal,
  },
  {
    id: "skills",
    label: "Skills",
    detail: "Reusable workflows and specialist behavior",
    icon: Sparkles,
  },
  {
    id: "memory",
    label: "Memory",
    detail: "Saved facts, review queue, and project boundaries",
    icon: Brain,
  },
  {
    id: "connectors",
    label: "Connectors",
    detail: "External accounts and tool access",
    icon: Cable,
  },
  {
    id: "activity",
    label: "Activity & permissions",
    detail: "Recent runs, permission decisions, and skill health",
    icon: History,
  },
]

export function CustomizeSurface({
  currentSessionId,
  onBack,
  onCreateSkillChat,
  onSelectSkill,
  onSkillsChanged,
  pendingPermissionRequest,
  skills = [],
}: CustomizeSurfaceProps) {
  const [customizeView, setCustomizeView] = useState<CustomizeView>("overview")
  const activeSkills = useMemo(() => skills.filter((skill) => skill.status === "active").length, [skills])
  const reviewSkills = useMemo(() => skills.filter((skill) => skill.status === "review").length, [skills])

  if (customizeView === "skills") {
    return (
      <SkillBrowser
        backLabel="Customize"
        onBack={() => setCustomizeView("overview")}
        onCreateSkillChat={onCreateSkillChat}
        onSelectSkill={onSelectSkill}
        onSkillsChanged={onSkillsChanged}
        skills={skills}
      />
    )
  }

  if (customizeView === "memory") {
    return (
      <div className="customize-surface">
        <CustomizeTopbar backLabel="Customize" onBack={() => setCustomizeView("overview")} title="Memory" />
        <main className="customize-memory-page">
          <MemoryBrowser />
        </main>
      </div>
    )
  }

  if (customizeView === "personalization") {
    return (
      <div className="customize-surface">
        <CustomizeTopbar backLabel="Customize" onBack={() => setCustomizeView("overview")} title="Personalization" />
        <main className="customize-detail-page">
          <PersonalizationPanel />
        </main>
      </div>
    )
  }

  if (customizeView === "connectors") {
    return (
      <div className="customize-surface">
        <CustomizeTopbar backLabel="Customize" onBack={() => setCustomizeView("overview")} title="Connectors" />
        <main className="customize-detail-page">
          <ConnectorsPanel />
        </main>
      </div>
    )
  }

  if (customizeView === "activity") {
    return (
      <div className="customize-surface">
        <CustomizeTopbar backLabel="Customize" onBack={() => setCustomizeView("overview")} title="Activity & permissions" />
        <main className="customize-detail-page">
          <ActivityCenter
            pendingPermissionRequest={pendingPermissionRequest}
            sessionId={currentSessionId}
            skills={skills}
          />
        </main>
      </div>
    )
  }

  return (
    <div className="customize-surface">
      <CustomizeTopbar onBack={onBack} title="Customize" />
      <main className="customize-shell">
        <aside aria-label="Customize sections" className="customize-nav">
          {CUSTOMIZE_NAV.map((item) => {
            const Icon = item.icon
            const active = customizeView === item.id
            return (
              <button
                aria-current={active ? "page" : undefined}
                className={cn(active && "active")}
                key={item.id}
                onClick={() => setCustomizeView(item.id)}
                type="button"
              >
                <Icon className="size-4" />
                <span>{item.label}</span>
              </button>
            )
          })}
        </aside>

        <section className="customize-main" aria-label="Customize overview">
          <div className="customize-heading">
            <p>Geneva</p>
            <h1>Customize</h1>
          </div>

          <div className="customize-overview-list">
            {CUSTOMIZE_NAV.map((item) => {
              const Icon = item.icon
              const meta =
                item.id === "skills"
                  ? `${activeSkills} active · ${reviewSkills} review`
                  : item.id === "activity"
                    ? pendingPermissionRequest
                      ? "Permission waiting"
                      : currentSessionId
                        ? "Current chat"
                        : "No chat selected"
                  : "Available"
              return (
                <button
                  className="customize-overview-row"
                  key={item.id}
                  onClick={() => setCustomizeView(item.id)}
                  type="button"
                >
                  <span className="customize-overview-icon">
                    <Icon className="size-4" />
                  </span>
                  <span className="customize-overview-copy">
                    <strong>{item.label}</strong>
                    <small>{item.detail}</small>
                  </span>
                  <span className="customize-overview-meta">{meta}</span>
                  <ChevronRight className="size-4" />
                </button>
              )
            })}
          </div>
        </section>
      </main>
    </div>
  )
}

function PersonalizationPanel() {
  return (
    <section className="customize-detail-panel" aria-label="Personalization">
      <div className="customize-heading">
        <p>Geneva</p>
        <h1>Personalization</h1>
      </div>
      <div className="customize-settings-list">
        <div className="customize-setting-row">
          <MessageSquareText className="size-4" />
          <div>
            <strong>Response style</strong>
            <span>Calm, direct, Claude-like, with restrained Geneva green accents in UI surfaces.</span>
          </div>
        </div>
        <div className="customize-setting-row">
          <Brain className="size-4" />
          <div>
            <strong>Memory behavior</strong>
            <span>High-confidence facts can save quietly; uncertain writes go through review and can be undone.</span>
          </div>
        </div>
        <div className="customize-setting-row">
          <CircleGauge className="size-4" />
          <div>
            <strong>Default effort</strong>
            <span>New chats start from the default mode configured in Settings. The composer can override per turn.</span>
          </div>
        </div>
        <div className="customize-setting-row">
          <ShieldCheck className="size-4" />
          <div>
            <strong>Boundaries</strong>
            <span>Project sources stay references. Personal memory stays separate from imported files and URLs.</span>
          </div>
        </div>
      </div>
    </section>
  )
}

function ConnectorsPanel() {
  return (
    <section className="customize-detail-panel" aria-label="Connectors">
      <div className="customize-heading">
        <p>Geneva</p>
        <h1>Connectors</h1>
      </div>
      <ConnectorsManager />
    </section>
  )
}

function CustomizeTopbar({
  backLabel = "Chat",
  onBack,
  title,
}: {
  backLabel?: string
  onBack: () => void
  title: string
}) {
  return (
    <header className="customize-topbar">
      <button className="skill-back-button" onClick={onBack} type="button">
        <ArrowLeft className="size-4" />
        <span>{backLabel}</span>
      </button>
      <span>{title}</span>
    </header>
  )
}
