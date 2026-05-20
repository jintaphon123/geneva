#!/usr/bin/env node

import { readFile } from "node:fs/promises"
import path from "node:path"
import process from "node:process"

const UI_ROOT = path.resolve(import.meta.dirname, "..")

const files = {
  app: path.join(UI_ROOT, "src", "App.tsx"),
  customize: path.join(UI_ROOT, "src", "components", "CustomizeSurface.tsx"),
  settings: path.join(UI_ROOT, "src", "components", "Settings.tsx"),
  settingsCss: path.join(UI_ROOT, "src", "styles", "settings.css"),
  skillsCss: path.join(UI_ROOT, "src", "styles", "skills-control-plane.css"),
  memoryCss: path.join(UI_ROOT, "src", "styles", "memory-browser.css"),
  apiIndex: path.join(UI_ROOT, "src", "lib", "api.ts"),
  connectorApi: path.join(UI_ROOT, "src", "lib", "api", "connector-api.ts"),
  modeApi: path.join(UI_ROOT, "src", "lib", "api", "mode-api.ts"),
  usageApi: path.join(UI_ROOT, "src", "lib", "api", "usage-api.ts"),
  onboardingApi: path.join(UI_ROOT, "src", "lib", "api", "onboarding-api.ts"),
  memoryBrowser: path.join(UI_ROOT, "src", "components", "MemoryBrowser.tsx"),
}

async function safeRead(file) {
  try {
    return await readFile(file, "utf8")
  } catch {
    return ""
  }
}

const [
  app,
  customize,
  settings,
  settingsCss,
  skillsCss,
  memoryCss,
  apiIndex,
  connectorApi,
  modeApi,
  usageApi,
  onboardingApi,
  memoryBrowser,
] = await Promise.all(
  Object.values(files).map(safeRead),
)

const checks = [
  {
    name: "Customize tab renders a Customize hub instead of opening SkillBrowser directly",
    pass:
      /import \{ CustomizeSurface \}/.test(app) &&
      /<CustomizeSurface/.test(app) &&
      !/activeTab === "skill" \? \(\s*<SkillBrowser/.test(app),
  },
  {
    name: "Customize hub exposes Claude-like IA sections",
    pass:
      /export function CustomizeSurface/.test(customize) &&
      /Personalization/.test(customize) &&
      /Skills/.test(customize) &&
      /Memory/.test(customize) &&
      /Connectors/.test(customize),
  },
  {
    name: "Customize Personalization and Connectors are real navigable surfaces, not disabled placeholders",
    pass:
      /PersonalizationPanel/.test(customize) &&
      /ConnectorsPanel/.test(customize) &&
      /ConnectorsManager/.test(customize) &&
      !/enabled:\s*false/.test(customize) &&
      !/disabled=\{!item\.enabled\}/.test(customize),
  },
  {
    name: "Customize hub keeps real Skills and Memory surfaces mounted behind IA choices",
    pass:
      /<SkillBrowser/.test(customize) &&
      /<MemoryBrowser/.test(customize) &&
      /customizeView/.test(customize),
  },
  {
    name: "Settings uses an internal navigation layout",
    pass:
      /settings-layout/.test(settings) &&
      /settings-nav/.test(settings) &&
      /href="#settings-api"/.test(settings) &&
      /href="#settings-modes"/.test(settings) &&
      /href="#settings-usage"/.test(settings) &&
      /href="#settings-connectors"/.test(settings) &&
      /href="#settings-onboarding"/.test(settings) &&
      /href="#settings-memory"/.test(settings),
  },
  {
    name: "Settings sections have stable ids for API, modes, usage, appearance, CLI, memory, skills, connectors, onboarding, and about",
    pass:
      /id="settings-api"/.test(settings) &&
      /id="settings-modes"/.test(settings) &&
      /id="settings-usage"/.test(settings) &&
      /id="settings-appearance"/.test(settings) &&
      /id="settings-cli"/.test(settings) &&
      /id="settings-memory"/.test(settings) &&
      /id="settings-skills"/.test(settings) &&
      /id="settings-connectors"/.test(settings) &&
      /id="settings-onboarding"/.test(settings) &&
      /id="settings-about"/.test(settings),
  },
  {
    name: "Settings uses real mode, connector, usage, and onboarding contracts",
    pass:
      /fetchModes/.test(settings) &&
      /ConnectorsManager/.test(settings) &&
      /fetchUsage/.test(settings) &&
      /fetchOnboardingStatus/.test(settings) &&
      /default_mode/.test(settings) &&
      /OnboardingModal/.test(settings),
  },
  {
    name: "MemoryBrowser exposes memory write review events, approve, and undo",
    pass:
      /listMemoryWriteEvents/.test(memoryBrowser) &&
      /approveMemoryWriteEvent/.test(memoryBrowser) &&
      /undoMemoryWriteEvent/.test(memoryBrowser) &&
      /MemoryWriteReviewQueue/.test(memoryBrowser),
  },
  {
    name: "UI-3 API helpers are exported for modes, connectors, usage, and onboarding",
    pass:
      /fetchModes/.test(modeApi) &&
      /fetchConnectors/.test(connectorApi) &&
      /configureConnector/.test(connectorApi) &&
      /deleteConnector/.test(connectorApi) &&
      /fetchUsage/.test(usageApi) &&
      /fetchOnboardingStatus/.test(onboardingApi) &&
      /from ['"]\.\/api\/mode-api['"]/.test(apiIndex) &&
      /from ['"]\.\/api\/connector-api['"]/.test(apiIndex) &&
      /from ['"]\.\/api\/usage-api['"]/.test(apiIndex) &&
      /from ['"]\.\/api\/onboarding-api['"]/.test(apiIndex),
  },
  {
    name: "UI-3 layout styles are present and stay restrained",
    pass:
      /\.settings-layout/.test(settingsCss) &&
      /\.settings-nav/.test(settingsCss) &&
      /\.customize-surface/.test(skillsCss) &&
      /\.customize-nav/.test(skillsCss) &&
      /\.customize-overview-row/.test(skillsCss),
  },
  {
    name: "MemoryBrowser is text-clean list-first, not a heavy auto-filled card grid",
    pass:
      /\.memory-list\s*\{[\s\S]*grid-template-columns:\s*1fr/.test(memoryCss) &&
      !/grid-template-columns:\s*repeat\(auto-fill/.test(memoryCss) &&
      /\.memory-card\s*\{[\s\S]*border-bottom:/.test(memoryCss) &&
      /\.memory-card:hover\s*\{[\s\S]*transform:\s*none/.test(memoryCss),
  },
]

const failed = checks.filter((check) => !check.pass)

if (failed.length) {
  console.error("UI-3 customize/settings check failed:")
  for (const check of failed) {
    console.error(`- ${check.name}`)
  }
  process.exit(1)
}

console.log(`UI-3 customize/settings check passed (${checks.length} checks)`)
