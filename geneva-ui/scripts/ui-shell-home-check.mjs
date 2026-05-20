#!/usr/bin/env node

import { readFile } from "node:fs/promises"
import path from "node:path"
import process from "node:process"

const UI_ROOT = path.resolve(import.meta.dirname, "..")

const files = {
  app: path.join(UI_ROOT, "src", "App.tsx"),
  sidebar: path.join(UI_ROOT, "src", "components", "Sidebar.tsx"),
  empty: path.join(UI_ROOT, "src", "components", "ChatEmptyState.tsx"),
  canvas: path.join(UI_ROOT, "src", "components", "ChatCanvas.tsx"),
  foundation: path.join(UI_ROOT, "src", "styles", "foundation.css"),
  chat: path.join(UI_ROOT, "src", "styles", "chat.css"),
}

const [app, sidebar, empty, canvas, foundation, chat] = await Promise.all(
  Object.values(files).map((file) => readFile(file, "utf8")),
)

const checks = [
  {
    name: "expanded sidebar exposes Search as a top-level row, not only a header icon",
    pass: /sidebar-search-action/.test(sidebar) && /onClick=\{onOpenSearch\}/.test(sidebar),
  },
  {
    name: "collapsed rail starts with a quiet Geneva brand anchor",
    pass: /sidebar-rail-brand/.test(sidebar) && /GenevaMark[^>]+variant="dot"/.test(sidebar),
  },
  {
    name: "recents show about 30 chats before the All Chats affordance",
    pass: /INITIAL_SESSION_LIMIT\s*=\s*30/.test(sidebar) && /All Chats/.test(sidebar),
  },
  {
    name: "home mark sits above the greeting per Bond's UI-1 preference",
    pass:
      /className="empty-mark"/.test(empty) &&
      !/empty-greeting-row/.test(empty) &&
      /\.empty-mark \.geneva-mark-svg\s*\{[\s\S]*width:\s*96px/.test(chat),
  },
  {
    name: "empty home removes the duplicate New chat header label",
    pass: /empty-chat-header/.test(canvas) && /empty-chat-header/.test(chat),
  },
  {
    name: "home display typography keeps neutral letter spacing",
    pass: /\.empty-state h1\s*\{[\s\S]*letter-spacing:\s*0\s*;/.test(chat),
  },
  {
    name: "home does not show Continue where you left off per Bond's latest preference",
    pass:
      !/continue-where-left-off/.test(canvas) &&
      !/recentSessions/.test(canvas) &&
      !/onContinueSession/.test(canvas) &&
      !/recentSessions=\{/.test(app) &&
      !/onContinueSession=\{handleSelectSession\}/.test(app),
  },
  {
    name: "rail buttons use stable icon dimensions",
    pass:
      /\.sidebar-rail-button\s*\{[\s\S]*width:\s*38px/.test(foundation) &&
      /\.sidebar-rail-button\s*\{[\s\S]*height:\s*38px/.test(foundation),
  },
]

const failed = checks.filter((check) => !check.pass)

if (failed.length) {
  console.error("UI shell/home check failed:")
  for (const check of failed) {
    console.error(`- ${check.name}`)
  }
  process.exit(1)
}

console.log(`UI shell/home check passed (${checks.length} checks)`)
