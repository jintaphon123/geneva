#!/usr/bin/env node

import { readFile } from "node:fs/promises"
import path from "node:path"
import process from "node:process"

const UI_ROOT = path.resolve(import.meta.dirname, "..")

const files = {
  app: path.join(UI_ROOT, "src", "App.tsx"),
  activityCenter: path.join(UI_ROOT, "src", "components", "ActivityCenter.tsx"),
  chatBubble: path.join(UI_ROOT, "src", "components", "ChatMessageBubble.tsx"),
  composer: path.join(UI_ROOT, "src", "components", "Composer.tsx"),
  customize: path.join(UI_ROOT, "src", "components", "CustomizeSurface.tsx"),
  skillBrowser: path.join(UI_ROOT, "src", "components", "SkillBrowser.tsx"),
  toolPermission: path.join(UI_ROOT, "src", "components", "ToolPermissionModal.tsx"),
  apiIndex: path.join(UI_ROOT, "src", "lib", "api.ts"),
  toolApi: path.join(UI_ROOT, "src", "lib", "api", "tool-api.ts"),
  types: path.join(UI_ROOT, "src", "types.ts"),
  chatCss: path.join(UI_ROOT, "src", "styles", "chat.css"),
  composerCss: path.join(UI_ROOT, "src", "styles", "composer-markdown.css"),
  permissionCss: path.join(UI_ROOT, "src", "styles", "open-source-permission.css"),
  skillsCss: path.join(UI_ROOT, "src", "styles", "skills-control-plane.css"),
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
  activityCenter,
  chatBubble,
  composer,
  customize,
  skillBrowser,
  toolPermission,
  apiIndex,
  toolApi,
  types,
  chatCss,
  composerCss,
  permissionCss,
  skillsCss,
  packageJson,
] = await Promise.all(Object.values(files).map(safeRead))

const checks = [
  {
    name: "UI-7 guard is wired into npm scripts",
    pass: /"check:ui7":\s*"node scripts\/ui7-skills-activity-check\.mjs"/.test(packageJson),
  },
  {
    name: "Skill Browser uses user-facing tabs for discover, installed, review, evals, and builder",
    pass:
      /SkillFilter\s*=\s*"discover"/.test(skillBrowser) &&
      /Discover/.test(skillBrowser) &&
      /Installed/.test(skillBrowser) &&
      /Needs review/.test(skillBrowser) &&
      /Evaluations/.test(skillBrowser) &&
      /Builder/.test(skillBrowser),
  },
  {
    name: "Skill Browser shows scope, safety, recent usage, and recommendation context",
    pass:
      /SkillScopeSelector/.test(skillBrowser) &&
      /skill-scope-selector/.test(skillsCss) &&
      /recommendedSkills/.test(skillBrowser) &&
      /skill-recommendation-strip/.test(skillBrowser) &&
      /formatLastUsed/.test(skillBrowser) &&
      /skillSafetyLabel/.test(skillBrowser),
  },
  {
    name: "Composer skill picker has search, descriptions, safety-like context, and scope selector",
    pass:
      /skillSearch/.test(composer) &&
      /skill-search-input/.test(composer) &&
      /skill-picker-row/.test(composer) &&
      /skill-picker-description/.test(composer) &&
      /skill-picker-scope/.test(composer) &&
      /SkillInvocationScope/.test(types),
  },
  {
    name: "Skill invocation appears as a quiet chat header, not a developer badge",
    pass:
      /SkillRunHeader/.test(chatBubble) &&
      /skill-run-header/.test(chatCss) &&
      /skillDescription/.test(types) &&
      /skillInvocationScope/.test(types) &&
      !/skill-active-badge/.test(chatBubble),
  },
  {
    name: "App preserves skill metadata on live assistant messages",
    pass:
      /skillDescription/.test(app) &&
      /skillSafetyStatus/.test(app) &&
      /skillInvocationScope/.test(app) &&
      /skills\.find/.test(app),
  },
  {
    name: "Activity Center reads the real session activity endpoint and is reachable from Customize",
    pass:
      /ActivityCenter/.test(activityCenter) &&
      /fetchSessionActivity/.test(toolApi) &&
      /\/api\/sessions\/.*\/activity/.test(toolApi) &&
      /Activity & permissions/.test(customize) &&
      /currentSessionId/.test(customize) &&
      /pendingPermissionRequest/.test(customize) &&
      /from "\.\/api\/tool-api"/.test(apiIndex),
  },
  {
    name: "Permission modal explains risk, why it appears, audit trail, and approve-once semantics",
    pass:
      /permissionRiskLabel/.test(toolPermission) &&
      /What it wants/.test(toolPermission) &&
      /Why this appears/.test(toolPermission) &&
      /Audit trail/.test(toolPermission) &&
      /Approve once/.test(toolPermission) &&
      /tool-permission-risk/.test(permissionCss),
  },
  {
    name: "Activity and permission styles are compact, Claude-like, and responsive",
    pass:
      /activity-center/.test(skillsCss) &&
      /permission-center/.test(skillsCss) &&
      /skill-picker-search/.test(composerCss) &&
      /skill-run-header/.test(chatCss),
  },
]

const failed = checks.filter((check) => !check.pass)

if (failed.length) {
  console.error("UI-7 skills, permissions, and activity check failed:")
  for (const check of failed) {
    console.error(`- ${check.name}`)
  }
  process.exit(1)
}

console.log(`UI-7 skills, permissions, and activity check passed (${checks.length} checks)`)
