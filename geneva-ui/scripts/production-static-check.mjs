#!/usr/bin/env node

import { gzipSync } from "node:zlib"
import { readdir, readFile } from "node:fs/promises"
import path from "node:path"
import process from "node:process"

const UI_ROOT = path.resolve(import.meta.dirname, "..")
const APP_ROOT = path.resolve(UI_ROOT, "..")
const SOURCE_ROOT = path.resolve(UI_ROOT, "src")
const BACKEND_SOURCE_ROOT = path.resolve(APP_ROOT, "src", "geneva")
const WEB_ASSET_ROOT = path.resolve(APP_ROOT, "src", "geneva", "web", "assets")
const SECURITY_MANIFEST_FILES = [
  path.resolve(APP_ROOT, "pyproject.toml"),
  path.resolve(APP_ROOT, "requirements.txt"),
]

const SOURCE_EXTENSIONS = new Set([".ts", ".tsx", ".js", ".jsx", ".css"])
const BACKEND_SOURCE_EXTENSIONS = new Set([".py"])
const BUNDLE_EXTENSIONS = new Set([".js", ".css"])
const BUDGETS = {
  largestJsGzipBytes: 72 * 1024,
  totalJsGzipBytes: 270 * 1024,
  largestCssGzipBytes: 38 * 1024,
}
const LINE_BUDGETS = new Map([
  ["geneva-ui/src/App.tsx", 1000],
  ["geneva-ui/src/components/SkillBrowser.tsx", 750],
  ["geneva-ui/src/components/SkillModals.tsx", 500],
  ["geneva-ui/src/components/ProjectView.tsx", 850],
  ["geneva-ui/src/components/ProjectViewSupport.tsx", 300],
  ["geneva-ui/src/components/ChatCanvas.tsx", 300],
  ["geneva-ui/src/components/ChatActivityPanel.tsx", 180],
  ["geneva-ui/src/components/ChatEmptyState.tsx", 110],
  ["geneva-ui/src/components/ChatMarkdown.tsx", 190],
  ["geneva-ui/src/components/ChatMessageBubble.tsx", 240],
  ["geneva-ui/src/components/ChatProgressRail.tsx", 160],
  ["geneva-ui/src/components/ChatStatusLine.tsx", 40],
  ["geneva-ui/src/lib/api.ts", 30],
  ["geneva-ui/src/lib/api/conversation-api.ts", 320],
  ["geneva-ui/src/lib/api/core.ts", 90],
  ["geneva-ui/src/lib/api/memory-api.ts", 220],
  ["geneva-ui/src/lib/api/project-api.ts", 140],
  ["geneva-ui/src/lib/api/settings-api.ts", 50],
  ["geneva-ui/src/lib/api/skill-api.ts", 220],
  ["geneva-ui/src/lib/api/stream-api.ts", 240],
  ["geneva-ui/src/lib/api/tool-api.ts", 70],
  ["geneva-ui/src/index.css", 30],
  ["geneva-ui/src/styles/project.css", 20],
  ["geneva-ui/src/styles/project-sidebar-chat.css", 430],
  ["geneva-ui/src/styles/project-workspace.css", 720],
  ["geneva-ui/src/styles/project-command-surface.css", 740],
  ["geneva-ui/src/styles/skills.css", 20],
  ["geneva-ui/src/styles/skills-control-plane.css", 920],
  ["geneva-ui/src/styles/skills-modals.css", 330],
  ["geneva-ui/src/styles/chat.css", 850],
  ["geneva-ui/src/styles/responsive.css", 750],
  ["geneva-ui/src/styles/memory-browser.css", 700],
  ["geneva-ui/src/styles/composer-markdown.css", 700],
  ["src/geneva/web_api.py", 520],
  ["src/geneva/web_runtime.py", 1050],
  ["src/geneva/session.py", 1300],
])

const forbiddenSourcePatterns = [
  {
    name: "browser confirm",
    pattern: /\b(?:window\.)?confirm\s*\(/,
    detail: "Use a designed confirmation modal; browser confirm feels unfinished and blocks the UI thread.",
  },
  {
    name: "browser alert",
    pattern: /\b(?:window\.)?alert\s*\(/,
    detail: "Use an inline error state or toast; alert boxes are not production UI.",
  },
  {
    name: "debugger statement",
    pattern: /\bdebugger\b/,
    detail: "Debugger statements must not ship in the production surface.",
  },
  {
    name: "dangerous HTML injection",
    pattern: /\bdangerouslySetInnerHTML\b/,
    detail: "Rendered user/AI content must pass through the markdown/sanitization path.",
  },
  {
    name: "settings secret placeholder",
    pattern: /placeholder=\{config\?\.\[[^\]]+\]/,
    detail: "Redacted API keys must never be rendered as input placeholder text.",
  },
  {
    name: "literal API key",
    pattern: /sk-[A-Za-z0-9_-]{20,}/,
    detail: "Secrets must live outside source control and never be hardcoded in UI source.",
  },
  {
    name: "wildcard CORS",
    pattern: /Access-Control-Allow-Origin["']?\s*[:=]\s*["']\*/i,
    detail: "Geneva local APIs must never allow wildcard CORS.",
  },
  {
    name: "unsafe dev bind",
    pattern: /--host\s+0\.0\.0\.0|host:\s*["']0\.0\.0\.0["']/,
    detail: "The local web surface must not bind to every interface by default.",
  },
  {
    name: "vulnerable zhipuai dependency",
    pattern: /\bzhipuai\b/i,
    detail: "The current zhipuai SDK pins PyJWT below the audited safe range; use the OpenAI-compatible GLM provider instead.",
  },
]

async function main() {
  const sourceFiles = [
    ...(await collectFiles(SOURCE_ROOT, SOURCE_EXTENSIONS)),
    ...(await collectFiles(BACKEND_SOURCE_ROOT, BACKEND_SOURCE_EXTENSIONS)),
    ...SECURITY_MANIFEST_FILES,
  ]
  const sourceFindings = await scanSourceFiles(sourceFiles)
  const lineBudgetFindings = await scanLineBudgets(sourceFiles)
  const bundleSummary = await checkBundleBudgets()
  const failures = [...sourceFindings, ...lineBudgetFindings, ...bundleSummary.failures]

  if (failures.length > 0) {
    console.error("\nProduction static check failed:")
    for (const failure of failures) {
      console.error(`- ${failure}`)
    }
    process.exitCode = 1
    return
  }

  console.log(
    [
      "production static check passed",
      `${sourceFiles.length} source files scanned`,
      `largest JS gzip ${formatBytes(bundleSummary.largestJsGzipBytes)}`,
      `total JS gzip ${formatBytes(bundleSummary.totalJsGzipBytes)}`,
      `largest CSS gzip ${formatBytes(bundleSummary.largestCssGzipBytes)}`,
    ].join(" | "),
  )
}

async function scanSourceFiles(files) {
  const findings = []
  for (const file of files) {
    const text = await readFile(file, "utf8")
    for (const check of forbiddenSourcePatterns) {
      const match = check.pattern.exec(text)
      if (match) {
        const line = lineForIndex(text, match.index)
        findings.push(`${relative(file)}:${line} ${check.name}: ${check.detail}`)
      }
    }
  }
  return findings
}

async function scanLineBudgets(files) {
  const findings = []
  for (const file of files) {
    const budget = LINE_BUDGETS.get(relative(file))
    if (budget === undefined) continue
    const text = await readFile(file, "utf8")
    const lineCount = text.split(/\r\n|\r|\n/).length
    if (lineCount > budget) {
      findings.push(`${relative(file)} has ${lineCount} lines; architecture budget is ${budget}`)
    }
  }
  return findings
}

async function checkBundleBudgets() {
  const assetFiles = await collectFiles(WEB_ASSET_ROOT, BUNDLE_EXTENSIONS)
  const failures = []
  let largestJsGzipBytes = 0
  let totalJsGzipBytes = 0
  let largestCssGzipBytes = 0

  for (const file of assetFiles) {
    const bytes = await readFile(file)
    const gzipBytes = gzipSync(bytes).length
    if (file.endsWith(".js")) {
      largestJsGzipBytes = Math.max(largestJsGzipBytes, gzipBytes)
      totalJsGzipBytes += gzipBytes
    }
    if (file.endsWith(".css")) {
      largestCssGzipBytes = Math.max(largestCssGzipBytes, gzipBytes)
    }
  }

  if (largestJsGzipBytes > BUDGETS.largestJsGzipBytes) {
    failures.push(
      `largest JS chunk gzip ${formatBytes(largestJsGzipBytes)} exceeds ${formatBytes(BUDGETS.largestJsGzipBytes)}`,
    )
  }
  if (totalJsGzipBytes > BUDGETS.totalJsGzipBytes) {
    failures.push(`total JS gzip ${formatBytes(totalJsGzipBytes)} exceeds ${formatBytes(BUDGETS.totalJsGzipBytes)}`)
  }
  if (largestCssGzipBytes > BUDGETS.largestCssGzipBytes) {
    failures.push(
      `largest CSS gzip ${formatBytes(largestCssGzipBytes)} exceeds ${formatBytes(BUDGETS.largestCssGzipBytes)}`,
    )
  }

  return {
    failures,
    largestCssGzipBytes,
    largestJsGzipBytes,
    totalJsGzipBytes,
  }
}

async function collectFiles(root, extensions) {
  const entries = await readdir(root, { withFileTypes: true })
  const files = []
  for (const entry of entries) {
    const fullPath = path.join(root, entry.name)
    if (entry.isDirectory()) {
      files.push(...(await collectFiles(fullPath, extensions)))
      continue
    }
    if (extensions.has(path.extname(entry.name))) {
      files.push(fullPath)
    }
  }
  return files.sort()
}

function lineForIndex(text, index) {
  return text.slice(0, index).split("\n").length
}

function relative(file) {
  return path.relative(APP_ROOT, file)
}

function formatBytes(bytes) {
  return `${(bytes / 1024).toFixed(1)} KiB`
}

await main()
