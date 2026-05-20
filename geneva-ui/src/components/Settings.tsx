import { type Dispatch, type ReactNode, type SetStateAction, useEffect, useState } from "react"
import {
  ArrowLeft,
  AlertCircle,
  BarChart3,
  Brain,
  Check,
  CheckCircle2,
  Cpu,
  Database,
  Eye,
  EyeOff,
  Info,
  KeyRound,
  Link2,
  Monitor,
  Moon,
  PlayCircle,
  RefreshCcw,
  Sun,
  TerminalSquare,
  XCircle,
} from "lucide-react"

import { ConnectorsManager } from "@/components/ConnectorsManager"
import { MemoryBrowser } from "@/components/MemoryBrowser"
import { OnboardingModal } from "@/components/OnboardingModal"
import { Button } from "@/components/ui/button"
import {
  fetchModes,
  fetchMemoryBrowserStats,
  fetchOnboardingStatus,
  fetchSettings,
  fetchSystemStatus,
  fetchUsage,
  importFromMyBrain,
  rebuildMemoryIndex,
  reloadSkills,
  saveSettingsField,
} from "@/lib/api"
import type { ThemeMode } from "@/lib/theme"
import type { MemoryBrowserStats, ModeProfile, OnboardingStatus, SettingsConfig, SystemStatus, UsageSummary } from "@/types"

type SettingsProps = {
  currentModeId: string
  effectiveDarkMode: boolean
  onClose: () => void
  onDefaultModeChange?: (modeId: "low" | "medium" | "high" | "extra_high") => void
  onThemeModeChange: (mode: ThemeMode) => void
  themeMode: ThemeMode
}

type ApiKeyField = "anthropic_api_key" | "openrouter_api_key" | "google_api_key"
type ModelField = "default_model" | "research_model" | "fast_model"

const API_KEY_FIELDS: Array<{
  field: ApiKeyField
  label: string
  note?: string
  placeholder: string
}> = [
  {
    field: "openrouter_api_key",
    label: "OpenRouter API Key",
    note: "OpenRouter key for DeepSeek V4. Save once, then chat immediately.",
    placeholder: "sk-or-v1-...",
  },
  {
    field: "anthropic_api_key",
    label: "Anthropic API Key",
    placeholder: "sk-ant-...",
  },
  {
    field: "google_api_key",
    label: "Google API Key",
    placeholder: "AIza...",
  },
]

const MODEL_PRESETS = [
  { value: "deepseek/deepseek-v4-flash", label: "DeepSeek v4 Flash (fast, cheap)" },
  { value: "claude-sonnet-4-6", label: "Claude Sonnet 4.6 (Anthropic)" },
  { value: "claude-haiku-4-5", label: "Claude Haiku 4.5 (Anthropic, fast)" },
  { value: "claude-opus-4-7", label: "Claude Opus 4.7 (Anthropic, most capable)" },
  { value: "gpt-5.4", label: "GPT-5.4 (OpenAI)" },
  { value: "gpt-4o-mini", label: "GPT-4o Mini (OpenAI, fast)" },
  { value: "google/gemini-2.5-pro", label: "Gemini 2.5 Pro (Google)" },
  { value: "google/gemini-2.5-flash", label: "Gemini 2.5 Flash (Google, fast)" },
]

const MODEL_FIELDS: Array<{ field: ModelField; label: string }> = [
  { field: "default_model", label: "Default Model" },
  { field: "research_model", label: "Research Model" },
  { field: "fast_model", label: "Fast Model" },
]

const APPEARANCE_OPTIONS: Array<{ value: ThemeMode; label: string; detail: string }> = [
  { value: "system", label: "System", detail: "Follow Mac appearance" },
  { value: "light", label: "Light", detail: "Bright Claude-style canvas" },
  { value: "dark", label: "Dark", detail: "Dim canvas for low light" },
]

const SELECT_CLASS_NAME =
  "min-w-0 flex-1 rounded-[8px] border border-[var(--border)] bg-[var(--card)] px-[11px] py-[9px] text-sm text-[var(--foreground)] outline-none focus:border-[var(--ring)] disabled:opacity-45"

function settingsErrorMessage(error: unknown, fallback: string) {
  const message = error instanceof Error ? error.message.trim() : ""
  const safeMessage = message.replace(/(?:sk-[A-Za-z0-9_-]+|AIza[0-9A-Za-z_-]+)/g, "redacted-key")
  if (!safeMessage) return fallback
  return safeMessage.length > 220 ? `${safeMessage.slice(0, 220)}...` : safeMessage
}

const EMPTY_USAGE: UsageSummary = {
  sessions_count: 0,
  entry_count: 0,
  total_tokens: 0,
  total_cost_usd: 0,
  by_model: [],
  recent_sessions: [],
}

export function Settings({
  currentModeId,
  effectiveDarkMode,
  onClose,
  onDefaultModeChange,
  onThemeModeChange,
  themeMode,
}: SettingsProps) {
  const [config, setConfig] = useState<SettingsConfig | null>(null)
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [modes, setModes] = useState<ModeProfile[]>([])
  const [usage, setUsage] = useState<UsageSummary>(EMPTY_USAGE)
  const [onboardingStatus, setOnboardingStatus] = useState<OnboardingStatus | null>(null)
  const [onboardingOpen, setOnboardingOpen] = useState(false)
  const [cli, setCli] = useState<{ gemini_ok: boolean; codex_ok: boolean } | null>(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState<string | null>(null)
  const [rebuilding, setRebuilding] = useState(false)
  const [localValues, setLocalValues] = useState<Record<string, string>>({})
  const [mybrainPath, setMybrainPath] = useState("")
  const [importingSkills, setImportingSkills] = useState(false)
  const [skillResult, setSkillResult] = useState<string | null>(null)
  const [memoryBrowserOpen, setMemoryBrowserOpen] = useState(false)
  const [memoryManagerStats, setMemoryManagerStats] = useState<MemoryBrowserStats>({})
  const [settingsError, setSettingsError] = useState<string | null>(null)
  const [visibleApiKeys, setVisibleApiKeys] = useState<Record<ApiKeyField, boolean>>({
    anthropic_api_key: false,
    openrouter_api_key: false,
    google_api_key: false,
  })

  useEffect(() => {
    void load()
  }, [])

  async function load() {
    try {
      const [settingsData, statusData, modesData, usageData, onboardingData] = await Promise.all([
        fetchSettings(),
        fetchSystemStatus(),
        fetchModes().catch(() => ({ default_mode_id: "medium", modes: [] })),
        fetchUsage().catch(() => EMPTY_USAGE),
        fetchOnboardingStatus().catch(() => ({ needs_onboarding: false, complete: false })),
      ])
      const managerStats = await fetchMemoryBrowserStats().catch(() => ({}))
      setConfig(settingsData.config)
      setCli(settingsData.cli)
      setStatus(statusData)
      setModes(modesData.modes)
      setUsage(usageData)
      setOnboardingStatus(onboardingData)
      setMemoryManagerStats(managerStats)
      setLocalValues({
        anthropic_api_key: "",
        openrouter_api_key: "",
        google_api_key: "",
        gemini_cli_path: settingsData.config.gemini_cli_path,
        codex_cli_path: settingsData.config.codex_cli_path,
      })
      setMybrainPath(settingsData.config.mybrain_dir || "")
      setSettingsError(null)
    } catch (error) {
      setSettingsError(settingsErrorMessage(error, "Settings could not be loaded."))
    }
  }

  async function saveField(field: string, value: string | boolean) {
    setSaving(true)
    setSettingsError(null)
    try {
      await saveSettingsField(field, value)
      if (field === "default_mode" && typeof value === "string") {
        const nextMode = normalizeModeId(value)
        onDefaultModeChange?.(nextMode)
      }
      setSaved(field)
      await load()
      window.setTimeout(() => setSaved((current) => (current === field ? null : current)), 1800)
    } catch (error) {
      setSettingsError(settingsErrorMessage(error, "Setting could not be saved."))
    } finally {
      setSaving(false)
    }
  }

  async function handleRebuild() {
    setRebuilding(true)
    setSettingsError(null)
    try {
      await rebuildMemoryIndex()
      setStatus(await fetchSystemStatus())
      setMemoryManagerStats(await fetchMemoryBrowserStats())
    } catch (error) {
      setSettingsError(settingsErrorMessage(error, "Memory index could not be rebuilt."))
    } finally {
      setRebuilding(false)
    }
  }

  async function handleImportSkills() {
    setImportingSkills(true)
    setSettingsError(null)
    try {
      const result = await importFromMyBrain(mybrainPath)
      await reloadSkills()
      setStatus(await fetchSystemStatus())
      await saveSettingsField("mybrain_dir", mybrainPath)
      setSkillResult(
        [
          `✓ ${result.skills_imported} skills imported`,
          `✓ ${result.context_imported} context files imported`,
          result.brain_md_created ? "✓ BRAIN.md created" : "BRAIN.md not found",
          ...result.errors.map((error) => `• ${error}`),
        ].join("\n"),
      )
    } catch (error) {
      setSettingsError(settingsErrorMessage(error, "MyBrain import could not be completed."))
    } finally {
      setImportingSkills(false)
    }
  }

  async function handleReloadSkills() {
    setSettingsError(null)
    try {
      const result = await reloadSkills()
      setStatus(await fetchSystemStatus())
      setSkillResult(`✓ ${result.count} skills loaded`)
    } catch (error) {
      setSettingsError(settingsErrorMessage(error, "Skills could not be reloaded."))
    }
  }

  return (
    <div className="settings-page">
      <div className="settings-header">
        <button className="settings-back" onClick={onClose} type="button">
          <ArrowLeft className="size-4" />
          Back
        </button>
        <h1>Settings</h1>
      </div>
      <div className="settings-body">
        {settingsError ? (
          <div className="settings-error-notice" role="alert">
            <AlertCircle className="size-4" />
            <span>{settingsError}</span>
            <button aria-label="Dismiss settings error" onClick={() => setSettingsError(null)} type="button">
              <XCircle className="size-4" />
            </button>
          </div>
        ) : null}
        <div className="settings-layout">
          <nav aria-label="Settings sections" className="settings-nav">
            <a href="#settings-api">API</a>
            <a href="#settings-modes">Modes</a>
            <a href="#settings-usage">Usage</a>
            <a href="#settings-appearance">Appearance</a>
            <a href="#settings-cli">CLI</a>
            <a href="#settings-memory">Memory</a>
            <a href="#settings-skills">Skills</a>
            <a href="#settings-connectors">Connectors</a>
            <a href="#settings-onboarding">Onboarding</a>
            <a href="#settings-about">About</a>
          </nav>
          <main className="settings-main">
        <SettingsSection id="settings-api" icon={<KeyRound className="size-4" />} title="API Configuration">
          {API_KEY_FIELDS.map((item) => {
            const pendingValue = localValues[item.field] ?? ""
            const hasStoredKey = Boolean(config?.[item.field])
            const isVisible = visibleApiKeys[item.field]
            return (
              <div className="settings-field" key={item.field}>
                <div className="settings-secret-heading">
                  <label>{item.label}</label>
                  <span className={hasStoredKey ? "settings-secret-status ok" : "settings-secret-status"}>
                    {hasStoredKey ? "Stored" : "Not configured"}
                  </span>
                </div>
                {item.note ? <p className="settings-note">{item.note}</p> : null}
                <div className="settings-input-row">
                  <input
                    aria-label={`${item.label} replacement`}
                    autoComplete="off"
                    onChange={(event) =>
                      setLocalValues((current) => ({ ...current, [item.field]: event.target.value }))
                    }
                    placeholder={hasStoredKey ? "Paste a new key to replace the stored key" : item.placeholder}
                    type={isVisible ? "text" : "password"}
                    value={pendingValue}
                  />
                  <Button
                    aria-label={`${isVisible ? "Hide" : "Show"} ${item.label}`}
                    onClick={() =>
                      setVisibleApiKeys((current) => ({ ...current, [item.field]: !current[item.field] }))
                    }
                    size="icon"
                    type="button"
                    variant="subtle"
                  >
                    {isVisible ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                  </Button>
                  <Button
                    disabled={saving || !pendingValue.trim()}
                    onClick={() => saveField(item.field, pendingValue.trim())}
                    type="button"
                  >
                    Save
                  </Button>
                </div>
                {saved === item.field ? <span className="saved-badge">Saved ✓</span> : null}
              </div>
            )
          })}
        </SettingsSection>

        <SettingsSection id="settings-modes" icon={<Cpu className="size-4" />} title="Modes">
          <ModeSettingsSection
            config={config}
            currentModeId={currentModeId}
            modes={modes}
            onSave={(modeId) => void saveField("default_mode", modeId)}
            saved={saved}
            saving={saving}
          />
          <div className="settings-subsection">
            <h3>Advanced model routing</h3>
            <p className="settings-note">Raw provider/model detail stays here; the composer keeps the simpler Mode control.</p>
          {MODEL_FIELDS.map((item) => (
            <div className="settings-field" key={item.field}>
              <label>{item.label}</label>
              <div className="settings-input-row">
                <select
                  className={SELECT_CLASS_NAME}
                  disabled={saving || !config}
                  onChange={(event) => saveField(item.field, event.target.value)}
                  value={config?.[item.field] ?? MODEL_PRESETS[0].value}
                >
                  {MODEL_PRESETS.map((model) => (
                    <option key={model.value} value={model.value}>
                      {model.label}
                    </option>
                  ))}
                </select>
              </div>
              {saved === item.field ? <span className="saved-badge">Saved ✓</span> : null}
            </div>
          ))}
          </div>
        </SettingsSection>

        <SettingsSection id="settings-usage" icon={<BarChart3 className="size-4" />} title="Usage">
          <UsageSection status={status} usage={usage} />
        </SettingsSection>

        <SettingsSection id="settings-appearance" icon={<Monitor className="size-4" />} title="Appearance">
          <div aria-label="Theme mode" className="settings-appearance-options" role="radiogroup">
            {APPEARANCE_OPTIONS.map((option) => (
              <button
                aria-checked={option.value === themeMode}
                className={option.value === themeMode ? "active" : undefined}
                key={option.value}
                onClick={() => onThemeModeChange(option.value)}
                role="radio"
                type="button"
              >
                <ThemeModeIcon mode={option.value} />
                <span>
                  <strong>{option.label}</strong>
                  <small>{option.detail}</small>
                </span>
                {option.value === themeMode ? <Check className="size-4" /> : null}
              </button>
            ))}
          </div>
          <p className="settings-note">
            Geneva is currently using {effectiveDarkMode ? "dark" : "light"} colors.
          </p>
        </SettingsSection>

        <SettingsSection id="settings-cli" icon={<TerminalSquare className="size-4" />} title="CLI Bridges">
          <CliField
            field="gemini_cli_path"
            label="Gemini CLI"
            localValues={localValues}
            ok={cli?.gemini_ok ?? false}
            onChange={setLocalValues}
            onSave={saveField}
            saved={saved}
            saving={saving}
          />
          <CliField
            field="codex_cli_path"
            label="Codex CLI"
            localValues={localValues}
            ok={cli?.codex_ok ?? false}
            onChange={setLocalValues}
            onSave={saveField}
            saved={saved}
            saving={saving}
          />
        </SettingsSection>

        <SettingsSection id="settings-memory" icon={<Database className="size-4" />} title="Memory">
          <MemoryManagerSection
            importing={importingSkills}
            memoryBrowserOpen={memoryBrowserOpen}
            mybrainPath={mybrainPath}
            onBrowse={() => setMemoryBrowserOpen(true)}
            onCloseBrowser={() => setMemoryBrowserOpen(false)}
            onImport={handleImportSkills}
            onPathChange={setMybrainPath}
            onRebuild={handleRebuild}
            rebuilding={rebuilding}
            stats={memoryManagerStats}
          />
        </SettingsSection>

        <SettingsSection id="settings-skills" icon={<Brain className="size-4" />} title="Skills">
          <div className="settings-field">
            <label>MyBrain path</label>
            <div className="settings-input-row">
              <input
                onChange={(event) => setMybrainPath(event.target.value)}
                value={mybrainPath}
              />
              <Button disabled={importingSkills} onClick={handleImportSkills} type="button">
                {importingSkills ? "Importing..." : "Import from MyBrain"}
              </Button>
            </div>
          </div>
          <div className="settings-stat-row">
            <span>{status?.skills_count ?? 0} skills loaded</span>
            <Button onClick={handleReloadSkills} type="button" variant="subtle">
              <RefreshCcw className="size-4" />
              Reload Skills
            </Button>
          </div>
        </SettingsSection>

        <SettingsSection id="settings-connectors" icon={<Link2 className="size-4" />} title="Connectors">
          <ConnectorsManager />
        </SettingsSection>

        <SettingsSection id="settings-onboarding" icon={<PlayCircle className="size-4" />} title="Onboarding">
          <OnboardingSettingsSection
            onStart={() => setOnboardingOpen(true)}
            status={onboardingStatus}
          />
        </SettingsSection>

        <SettingsSection id="settings-about" icon={<Info className="size-4" />} title="About">
          <p className="settings-about-line">Geneva v{status?.version ?? "0.3.0"}</p>
          <p className="settings-about-line">Running at {window.location.origin}</p>
        </SettingsSection>
          </main>
        </div>
      </div>
      {skillResult ? (
        <div className="settings-result-backdrop">
          <div className="settings-result-modal">
            <button aria-label="Close" onClick={() => setSkillResult(null)} type="button">
              <XCircle className="size-4" />
            </button>
            <pre>{skillResult}</pre>
          </div>
        </div>
      ) : null}
      <OnboardingModal
        onClose={() => setOnboardingOpen(false)}
        onComplete={() => {
          setOnboardingOpen(false)
          void load()
        }}
        open={onboardingOpen}
      />
    </div>
  )
}

function ModeSettingsSection({
  config,
  currentModeId,
  modes,
  onSave,
  saved,
  saving,
}: {
  config: SettingsConfig | null
  currentModeId: string
  modes: ModeProfile[]
  onSave: (modeId: string) => void
  saved: string | null
  saving: boolean
}) {
  const selectedMode = config?.default_mode || "medium"
  const visibleModes = modes.length
    ? modes
    : [
        {
          id: "medium",
          label: "Medium",
          description: "Balanced default",
          provider: "openrouter",
          primary_model: "deepseek/deepseek-v4-flash",
          fallback_model: "openrouter/free",
          context_budget_tokens: 64000,
          tool_autonomy: "guided",
          research_depth: "standard",
          cost_tier: "balanced",
          latency_tier: "balanced",
          background_policy: "manual",
          model: "deepseek/deepseek-v4-flash",
          default: true,
        },
      ]

  return (
    <>
      <div className="settings-field">
        <label>Default mode for new chats</label>
        <div className="settings-input-row">
          <select
            className={SELECT_CLASS_NAME}
            disabled={saving}
            onChange={(event) => onSave(event.target.value)}
            value={selectedMode}
          >
            {visibleModes.map((mode) => (
              <option key={mode.id} value={mode.id}>
                {mode.label}
              </option>
            ))}
          </select>
          <span className="settings-status ok">Current composer: {formatModeLabel(currentModeId)}</span>
        </div>
        {saved === "default_mode" ? <span className="saved-badge">Saved ✓</span> : null}
      </div>

      <div className="settings-mode-grid">
        {visibleModes.map((mode) => (
          <article className={mode.id === selectedMode ? "settings-mode-card active" : "settings-mode-card"} key={mode.id}>
            <div>
              <strong>{mode.label}</strong>
              <span>{mode.description}</span>
            </div>
            <dl>
              <div>
                <dt>Context</dt>
                <dd>{formatTokens(mode.context_budget_tokens)}</dd>
              </div>
              <div>
                <dt>Tools</dt>
                <dd>{formatCompactValue(mode.tool_autonomy)}</dd>
              </div>
              <div>
                <dt>Research</dt>
                <dd>{formatCompactValue(mode.research_depth)}</dd>
              </div>
              <div>
                <dt>Cost</dt>
                <dd>{formatCompactValue(mode.cost_tier)}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
    </>
  )
}

function UsageSection({ status, usage }: { status: SystemStatus | null; usage: UsageSummary }) {
  return (
    <>
      <div className="settings-usage-grid">
        <MetricCard label="Tokens" value={usage.total_tokens.toLocaleString()} />
        <MetricCard label="Cost" value={`$${usage.total_cost_usd.toFixed(4)}`} />
        <MetricCard label="Sessions" value={usage.sessions_count.toLocaleString()} />
        <MetricCard label="Entries" value={usage.entry_count.toLocaleString()} />
        <MetricCard label="Memories" value={(status?.memory_count ?? 0).toLocaleString()} />
        <MetricCard label="Skills" value={(status?.skills_count ?? 0).toLocaleString()} />
      </div>
      <div className="settings-usage-list">
        <h3>By model</h3>
        {usage.by_model.length ? (
          usage.by_model.map((row) => (
            <div className="settings-usage-row" key={row.model}>
              <span>{row.model}</span>
              <strong>{row.tokens.toLocaleString()} tokens · ${row.cost_usd.toFixed(4)}</strong>
            </div>
          ))
        ) : (
          <p className="settings-note">No local cost entries recorded yet.</p>
        )}
      </div>
    </>
  )
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="settings-metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function OnboardingSettingsSection({
  onStart,
  status,
}: {
  onStart: () => void
  status: OnboardingStatus | null
}) {
  const complete = Boolean(status?.complete)
  const needsOnboarding = Boolean(status?.needs_onboarding)
  return (
    <div className="settings-onboarding-panel">
      <div>
        <strong>{complete ? "Owner profile is complete" : needsOnboarding ? "Owner profile needs setup" : "Onboarding available"}</strong>
        <span>
          Run the owner interview when Geneva needs fresh instructions, personal context, or working preferences.
        </span>
      </div>
      <Button onClick={onStart} type="button">
        {complete ? "Run again" : "Start"}
      </Button>
      <div className="settings-onboarding-row">
        <span>Owner Manual preview / approve</span>
        <strong>Waiting for UX-B11 contract</strong>
      </div>
    </div>
  )
}

function MemoryManagerSection({
  importing,
  memoryBrowserOpen,
  mybrainPath,
  onBrowse,
  onCloseBrowser,
  onImport,
  onPathChange,
  onRebuild,
  rebuilding,
  stats,
}: {
  importing: boolean
  memoryBrowserOpen: boolean
  mybrainPath: string
  onBrowse: () => void
  onCloseBrowser: () => void
  onImport: () => void
  onPathChange: (path: string) => void
  onRebuild: () => void
  rebuilding: boolean
  stats: MemoryBrowserStats
}) {
  const byStatus = stats.by_status ?? {}
  const total =
    (byStatus.active ?? 0) +
    (byStatus.superseded ?? 0) +
    (byStatus.archived ?? 0) +
    (byStatus.expired ?? 0)

  return (
    <>
      <div className="settings-memory-chips">
        <span>{total} total</span>
        <span>{byStatus.active ?? 0} active</span>
        <span>{byStatus.superseded ?? 0} superseded</span>
        <span>{byStatus.archived ?? 0} archived</span>
        <span>{byStatus.expired ?? 0} expired</span>
      </div>
      <div className="settings-input-row settings-memory-actions">
        <Button onClick={onBrowse} type="button" variant="subtle">
          <Brain className="size-4" />
          Browse Memories
        </Button>
        <Button disabled={rebuilding} onClick={onRebuild} type="button" variant="subtle">
          <RefreshCcw className="size-4" />
          {rebuilding ? "Rebuilding..." : "Rebuild Index"}
        </Button>
      </div>
      <div className="settings-field">
        <label>Import memory context</label>
        <div className="settings-input-row">
          <input onChange={(event) => onPathChange(event.target.value)} value={mybrainPath} />
          <Button disabled={importing} onClick={onImport} type="button">
            {importing ? "Importing..." : "Import from MyBrain"}
          </Button>
        </div>
      </div>
      {memoryBrowserOpen ? (
        <div className="settings-memory-browser-modal">
          <div className="settings-memory-browser-panel">
            <button
              aria-label="Close memory browser"
              className="settings-memory-close"
              onClick={onCloseBrowser}
              type="button"
            >
              <XCircle className="size-4" />
            </button>
            <MemoryBrowser />
          </div>
        </div>
      ) : null}
    </>
  )
}

function CliField({
  field,
  label,
  localValues,
  ok,
  onChange,
  onSave,
  saved,
  saving,
}: {
  field: "gemini_cli_path" | "codex_cli_path"
  label: string
  localValues: Record<string, string>
  ok: boolean
  onChange: Dispatch<SetStateAction<Record<string, string>>>
  onSave: (field: string, value: string | boolean) => void
  saved: string | null
  saving: boolean
}) {
  return (
    <div className="settings-field">
      <label>{label}</label>
      <div className="settings-input-row">
        <input
          onChange={(event) => onChange((current) => ({ ...current, [field]: event.target.value }))}
          value={localValues[field] ?? ""}
        />
        <StatusBadge ok={ok} />
        <Button disabled={saving} onClick={() => onSave(field, localValues[field] ?? "")}>
          Save
        </Button>
      </div>
      {saved === field ? <span className="saved-badge">Saved ✓</span> : null}
    </div>
  )
}

function StatusBadge({ ok }: { ok: boolean }) {
  return (
    <span className={ok ? "settings-status ok" : "settings-status"}>
      {ok ? <CheckCircle2 className="size-3.5" /> : <XCircle className="size-3.5" />}
      {ok ? "Found" : "Not found"}
    </span>
  )
}

function ThemeModeIcon({ mode }: { mode: ThemeMode }) {
  if (mode === "system") return <Monitor className="size-4" />
  if (mode === "dark") return <Moon className="size-4" />
  return <Sun className="size-4" />
}

function normalizeModeId(modeId: string): "low" | "medium" | "high" | "extra_high" {
  const normalized = modeId.trim().toLowerCase().replace(/[-\s]+/g, "_")
  if (normalized === "low" || normalized === "medium" || normalized === "high" || normalized === "extra_high") {
    return normalized
  }
  return "medium"
}

function formatModeLabel(modeId: string): string {
  return normalizeModeId(modeId)
    .split("_")
    .map((part) => `${part.slice(0, 1).toUpperCase()}${part.slice(1)}`)
    .join(" ")
}

function formatCompactValue(value: string): string {
  return value
    .split(/[_-]+/)
    .filter(Boolean)
    .map((part) => `${part.slice(0, 1).toUpperCase()}${part.slice(1)}`)
    .join(" ")
}

function formatTokens(tokens: number): string {
  if (tokens >= 1000) return `${Math.round(tokens / 1000)}k`
  return tokens.toLocaleString()
}

function SettingsSection({
  children,
  icon,
  id,
  title,
}: {
  children: ReactNode
  icon: ReactNode
  id: string
  title: string
}) {
  return (
    <section className="settings-section" id={id}>
      <h2>
        {icon}
        {title}
      </h2>
      {children}
    </section>
  )
}
