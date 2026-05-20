#!/usr/bin/env node

import { readFile } from "node:fs/promises"
import path from "node:path"
import process from "node:process"

const UI_ROOT = path.resolve(import.meta.dirname, "..")

const files = {
  projectView: path.join(UI_ROOT, "src", "components", "ProjectView.tsx"),
  projectApi: path.join(UI_ROOT, "src", "lib", "api", "project-api.ts"),
  types: path.join(UI_ROOT, "src", "types.ts"),
  projectWorkspaceCss: path.join(UI_ROOT, "src", "styles", "project-workspace.css"),
  projectCommandCss: path.join(UI_ROOT, "src", "styles", "project-command-surface.css"),
  composer: path.join(UI_ROOT, "src", "components", "Composer.tsx"),
}

async function safeRead(file) {
  try {
    return await readFile(file, "utf8")
  } catch {
    return ""
  }
}

const [
  projectView,
  projectApi,
  types,
  projectWorkspaceCss,
  projectCommandCss,
  composer,
] = await Promise.all(Object.values(files).map(safeRead))

const allProjectCss = `${projectWorkspaceCss}\n${projectCommandCss}`

const checks = [
  {
    name: "Project workspace has real tab state and the UI-4 tab set",
    pass:
      /ProjectWorkspaceTab/.test(projectView) &&
      /activeTab/.test(projectView) &&
      /Overview/.test(projectView) &&
      /Conversations/.test(projectView) &&
      /Memories/.test(projectView) &&
      /Sources/.test(projectView) &&
      /Tasks/.test(projectView) &&
      /Artifacts/.test(projectView) &&
      /Settings/.test(projectView),
  },
  {
    name: "Project Sources tab is wired to the backend Project Sources contracts",
    pass:
      /fetchProjectSources/.test(projectView) &&
      /fetchProjectSourcePreview/.test(projectView) &&
      /addProjectTextSource/.test(projectView) &&
      /updateProjectSource/.test(projectView) &&
      /deleteProjectSource/.test(projectView) &&
      /\/api\/projects\/\$\{encodeURIComponent\(projectId\)\}\/sources/.test(projectApi),
  },
  {
    name: "Project source types and status model are represented in UI types",
    pass:
      /export type ProjectSource/.test(types) &&
      /parse_status/.test(types) &&
      /include_policy/.test(types) &&
      /ProjectSourcePreview/.test(types),
  },
  {
    name: "Sources UI shows truthful backend statuses and include/exclude controls",
    pass:
      /Ready/.test(projectView) &&
      /Parsing/.test(projectView) &&
      /Unsupported/.test(projectView) &&
      /Excluded/.test(projectView) &&
      /Stale/.test(projectView) &&
      /include_policy/.test(projectView),
  },
  {
    name: "Command rail language is replaced with Project plan and Project health",
    pass:
      !/Command rail/.test(projectView) &&
      /Project plan/.test(projectView) &&
      /Project health/.test(projectView),
  },
  {
    name: "Artifacts tab is wired to real project research reports after UI-6",
    pass:
      /ProjectArtifactsPanel/.test(projectView) &&
      /Deep Research reports saved while this project is attached/.test(projectView),
  },
  {
    name: "Project memory boundary copy is visible in the workspace",
    pass:
      /Project memory stays scoped/.test(projectView) &&
      /Personal memory remains separate/.test(projectView),
  },
  {
    name: "Global composer keeps the active project chip visible",
    pass:
      /composer-context-pill/.test(composer) &&
      /Project:/.test(composer) &&
      /activeProject/.test(composer),
  },
  {
    name: "UI-4 workspace styles are present and restrained",
    pass:
      /\.project-tabs/.test(allProjectCss) &&
      /\.project-tab-panel/.test(allProjectCss) &&
      /\.project-source-row/.test(allProjectCss) &&
      /\.project-health/.test(allProjectCss),
  },
]

const failed = checks.filter((check) => !check.pass)

if (failed.length) {
  console.error("UI-4 project workspace check failed:")
  for (const check of failed) {
    console.error(`- ${check.name}`)
  }
  process.exit(1)
}

console.log(`UI-4 project workspace check passed (${checks.length} checks)`)
