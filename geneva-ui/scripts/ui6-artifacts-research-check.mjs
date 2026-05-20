#!/usr/bin/env node

import { readFile } from "node:fs/promises"
import path from "node:path"
import process from "node:process"

const UI_ROOT = path.resolve(import.meta.dirname, "..")

const files = {
  app: path.join(UI_ROOT, "src", "App.tsx"),
  sidebar: path.join(UI_ROOT, "src", "components", "Sidebar.tsx"),
  chatMarkdown: path.join(UI_ROOT, "src", "components", "ChatMarkdown.tsx"),
  researchPlanCard: path.join(UI_ROOT, "src", "components", "ResearchPlanCard.tsx"),
  projectView: path.join(UI_ROOT, "src", "components", "ProjectView.tsx"),
  artifactsSurface: path.join(UI_ROOT, "src", "components", "ArtifactsSurface.tsx"),
  projectArtifactsPanel: path.join(UI_ROOT, "src", "components", "ProjectArtifactsPanel.tsx"),
  apiIndex: path.join(UI_ROOT, "src", "lib", "api.ts"),
  artifactApi: path.join(UI_ROOT, "src", "lib", "api", "artifact-api.ts"),
  researchApi: path.join(UI_ROOT, "src", "lib", "api", "research-api.ts"),
  streamApi: path.join(UI_ROOT, "src", "lib", "api", "stream-api.ts"),
  types: path.join(UI_ROOT, "src", "types.ts"),
  artifactsCss: path.join(UI_ROOT, "src", "styles", "artifacts.css"),
  indexCss: path.join(UI_ROOT, "src", "index.css"),
  packageJson: path.join(UI_ROOT, "package.json"),
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
  sidebar,
  chatMarkdown,
  researchPlanCard,
  projectView,
  artifactsSurface,
  projectArtifactsPanel,
  apiIndex,
  artifactApi,
  researchApi,
  streamApi,
  types,
  artifactsCss,
  indexCss,
  packageJson,
] = await Promise.all(Object.values(files).map(safeRead))

const checks = [
  {
    name: "UI-6 guard is wired into npm scripts",
    pass: /"check:ui6":\s*"node scripts\/ui6-artifacts-research-check\.mjs"/.test(packageJson),
  },
  {
    name: "Artifacts API is first-class and exported",
    pass:
      /fetchArtifacts/.test(artifactApi) &&
      /fetchArtifact/.test(artifactApi) &&
      /deleteArtifact/.test(artifactApi) &&
      /\/api\/artifacts/.test(artifactApi) &&
      /from "\.\/api\/artifact-api"/.test(apiIndex),
  },
  {
    name: "Research API exposes durable run list/detail/status contracts",
    pass:
      /fetchResearchRuns/.test(researchApi) &&
      /fetchResearchRun/.test(researchApi) &&
      /updateResearchRunStatus/.test(researchApi) &&
      /\/api\/research\/runs/.test(researchApi),
  },
  {
    name: "UI types model artifacts, research runs, sources, and completion artifact ids",
    pass:
      /export type ArtifactRecord/.test(types) &&
      /export type ArtifactDetail/.test(types) &&
      /export type ResearchRun/.test(types) &&
      /export type ResearchSource/.test(types) &&
      /researchArtifactId/.test(types) &&
      /researchSources/.test(types),
  },
  {
    name: "Research streaming preserves run_id/artifact_id/sources and can be stopped",
    pass:
      /runId/.test(streamApi) &&
      /artifactId/.test(streamApi) &&
      /sources/.test(streamApi) &&
      /qualityScore/.test(streamApi) &&
      /signal\?:\s*AbortSignal/.test(streamApi) &&
      /signal:\s*payload\.signal/.test(streamApi),
  },
  {
    name: "Sidebar Artifacts opens a real surface instead of a disabled placeholder",
    pass:
      /onOpenArtifacts/.test(sidebar) &&
      !/sidebar-artifacts-action" disabled/.test(sidebar) &&
      !/<RailButton disabled label="Artifacts"/.test(sidebar),
  },
  {
    name: "App mounts ArtifactsSurface and routes research completion into artifact metadata",
    pass:
      /ArtifactsSurface/.test(app) &&
      /showArtifacts/.test(app) &&
      /setShowArtifacts\(true\)/.test(app) &&
      /activeResearchAbortRef/.test(app) &&
      /researchArtifactId/.test(app),
  },
  {
    name: "Artifacts surface lists durable outputs with human labels and traceable detail",
    pass:
      /artifacts-surface/.test(artifactsSurface) &&
      /fetchArtifacts/.test(artifactsSurface) &&
      /fetchResearchRuns/.test(artifactsSurface) &&
      /artifactTypeLabel/.test(artifactsSurface) &&
      /Research report/.test(artifactsSurface) &&
      /Source trace/.test(artifactsSurface) &&
      /Copy text/.test(artifactsSurface) &&
      !/>research_report</.test(artifactsSurface) &&
      !/>research_trace</.test(artifactsSurface),
  },
  {
    name: "Project Artifacts tab reads real project research reports",
    pass:
      /ProjectArtifactsPanel/.test(projectView) &&
      /fetchResearchRuns/.test(projectArtifactsPanel) &&
      /fetchArtifact/.test(projectArtifactsPanel) &&
      !/Product Artifact Model \(UX-B3\) is not enabled yet/.test(projectView),
  },
  {
    name: "Deep Research plan/progress/report UI uses ChatGPT-like workflow language",
    pass:
      /Review plan/.test(researchPlanCard) &&
      /Start research/.test(researchPlanCard) &&
      /Edit plan/.test(researchPlanCard) &&
      /research-plan-step/.test(researchPlanCard) &&
      /research-progress-timeline/.test(chatMarkdown) &&
      /Saved as report artifact/.test(chatMarkdown),
  },
  {
    name: "UI-6 styles are imported and cover artifacts/research states responsively",
    pass:
      /@import "\.\/styles\/artifacts\.css";/.test(indexCss) &&
      /\.artifacts-surface/.test(artifactsCss) &&
      /\.artifact-detail/.test(artifactsCss) &&
      /\.research-progress-timeline/.test(artifactsCss) &&
      /@media \(max-width: 760px\)/.test(artifactsCss),
  },
]

const failed = checks.filter((check) => !check.pass)

if (failed.length) {
  console.error("UI-6 artifacts and research flow check failed:")
  for (const check of failed) {
    console.error(`- ${check.name}`)
  }
  process.exit(1)
}

console.log(`UI-6 artifacts and research flow check passed (${checks.length} checks)`)
