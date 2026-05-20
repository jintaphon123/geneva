#!/usr/bin/env node

import { readFile } from "node:fs/promises"
import path from "node:path"
import process from "node:process"

const UI_ROOT = path.resolve(import.meta.dirname, "..")

const files = {
  packageJson: path.join(UI_ROOT, "package.json"),
  composer: path.join(UI_ROOT, "src", "components", "Composer.tsx"),
  memoryBrowser: path.join(UI_ROOT, "src", "components", "MemoryBrowser.tsx"),
  projectView: path.join(UI_ROOT, "src", "components", "ProjectView.tsx"),
  responsiveCss: path.join(UI_ROOT, "src", "styles", "responsive.css"),
  artifactsCss: path.join(UI_ROOT, "src", "styles", "artifacts.css"),
  visualSmoke: path.join(UI_ROOT, "scripts", "visual-smoke.mjs"),
  productionQa: path.join(UI_ROOT, "scripts", "production-qa.mjs"),
  checklist: path.join(UI_ROOT, "docs", "ui8-production-qa-checklist.md"),
}

async function safeRead(file) {
  try {
    return await readFile(file, "utf8")
  } catch {
    return ""
  }
}

const [
  packageJson,
  composer,
  memoryBrowser,
  projectView,
  responsiveCss,
  artifactsCss,
  visualSmoke,
  productionQa,
  checklist,
] = await Promise.all(Object.values(files).map(safeRead))

const checks = [
  {
    name: "UI-8 guard is wired into npm scripts and production QA",
    pass:
      /"check:ui8":\s*"node scripts\/ui8-responsive-production-check\.mjs"/.test(packageJson) &&
      /check:ui8/.test(productionQa),
  },
  {
    name: "Composer collapses active context modes into one or two chips plus overflow",
    pass:
      /activeComposerPills/.test(composer) &&
      /visibleComposerPills/.test(composer) &&
      /hiddenComposerPillCount/.test(composer) &&
      /composer-active-pills/.test(composer) &&
      /composer-overflow-chip/.test(composer),
  },
  {
    name: "Project right rail becomes a mobile bottom sheet instead of a second stacked rail",
    pass:
      /mobileRailOpen/.test(projectView) &&
      /project-mobile-context-toggle/.test(projectView) &&
      /project-context-sheet-backdrop/.test(projectView) &&
      /project-context-mobile-sheet/.test(projectView) &&
      /Open project context/.test(projectView),
  },
  {
    name: "Memory Browser exposes a mobile filter drawer",
    pass:
      /mobileFiltersOpen/.test(memoryBrowser) &&
      /memory-mobile-filter-toggle/.test(memoryBrowser) &&
      /memory-filter-backdrop/.test(memoryBrowser) &&
      /memory-mobile-filter-close/.test(memoryBrowser),
  },
  {
    name: "Responsive CSS includes UI-8 overflow, bottom sheet, settings, and small-screen rules",
    pass:
      /\.ui8-overflow-safe/.test(responsiveCss) &&
      /\.mobile-bottom-sheet/.test(responsiveCss) &&
      /\.project-mobile-context-toggle/.test(responsiveCss) &&
      /\.project-context-mobile-sheet/.test(responsiveCss) &&
      /\.composer-active-pills/.test(responsiveCss) &&
      /\.composer-overflow-chip/.test(responsiveCss) &&
      /\.memory-mobile-filter-toggle/.test(responsiveCss) &&
      /\.settings-memory-browser-panel/.test(responsiveCss) &&
      /@media \(max-width: 480px\)/.test(responsiveCss),
  },
  {
    name: "Deep Research and artifact reports are readable on mobile",
    pass:
      /\.artifact-report-body pre/.test(artifactsCss) &&
      /\.research-card/.test(artifactsCss) &&
      /\.research-progress-row/.test(artifactsCss) &&
      /overflow-wrap:\s*anywhere/.test(artifactsCss),
  },
  {
    name: "Visual smoke validates UI-8 mobile no-overflow and project bottom sheet behavior",
    pass:
      /ui8MobileMetrics/.test(visualSmoke) &&
      /projectContextSheetOpen/.test(visualSmoke) &&
      /project-mobile-context-toggle/.test(visualSmoke) &&
      /horizontal overflow/.test(visualSmoke),
  },
  {
    name: "Production QA checklist captures UI-8 acceptance criteria",
    pass:
      /UI-8 Responsive, Polish, Production QA/.test(checklist) &&
      /No horizontal overflow/.test(checklist) &&
      /Mobile can start chat/.test(checklist) &&
      /Project right rail bottom sheet/.test(checklist) &&
      /Deep Research report/.test(checklist),
  },
]

const failed = checks.filter((check) => !check.pass)

if (failed.length) {
  console.error("UI-8 responsive production check failed:")
  for (const check of failed) {
    console.error(`- ${check.name}`)
  }
  process.exit(1)
}

console.log(`UI-8 responsive production check passed (${checks.length} checks)`)
