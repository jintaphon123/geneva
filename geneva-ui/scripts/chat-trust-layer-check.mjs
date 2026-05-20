#!/usr/bin/env node

import { readFile } from "node:fs/promises"
import path from "node:path"
import process from "node:process"

const UI_ROOT = path.resolve(import.meta.dirname, "..")

const files = {
  activity: path.join(UI_ROOT, "src", "components", "ChatActivityPanel.tsx"),
  bubble: path.join(UI_ROOT, "src", "components", "ChatMessageBubble.tsx"),
  canvas: path.join(UI_ROOT, "src", "components", "ChatCanvas.tsx"),
  app: path.join(UI_ROOT, "src", "App.tsx"),
  conversation: path.join(UI_ROOT, "src", "lib", "api", "conversation-api.ts"),
  mark: path.join(UI_ROOT, "src", "components", "GenevaMark.tsx"),
  statusLine: path.join(UI_ROOT, "src", "components", "ChatStatusLine.tsx"),
  types: path.join(UI_ROOT, "src", "types.ts"),
  foundation: path.join(UI_ROOT, "src", "styles", "foundation.css"),
  chat: path.join(UI_ROOT, "src", "styles", "chat.css"),
}

const [activity, bubble, canvas, app, conversation, mark, statusLine, types, foundation, chat] = await Promise.all(
  Object.values(files).map((file) => readFile(file, "utf8")),
)

function keyframesBlock(css, name) {
  const marker = `@keyframes ${name}`
  const start = css.indexOf(marker)
  if (start === -1) return ""
  const open = css.indexOf("{", start)
  if (open === -1) return ""
  let depth = 0
  for (let index = open; index < css.length; index += 1) {
    if (css[index] === "{") depth += 1
    if (css[index] === "}") {
      depth -= 1
      if (depth === 0) return css.slice(open + 1, index)
    }
  }
  return ""
}

function hasOpacityInKeyframes(css, name) {
  return /opacity\s*:/.test(keyframesBlock(css, name))
}

const checks = [
  {
    name: "activity panel stays collapsed by default unless a problem needs attention",
    pass:
      /useState\(\(\) => hasProblem\)/.test(activity) &&
      !/useState\(\(\) => loading \|\| hasProblem\)/.test(activity) &&
      !/if \(loading \|\| hasProblem\) setExpanded\(true\)/.test(activity),
  },
  {
    name: "activity tool titles use product-facing labels instead of raw class names",
    pass:
      /function formatToolLabel/.test(activity) &&
      /function formatActivityDetail/.test(activity) &&
      /formatToolLabel\(event\.toolName/.test(activity) &&
      /formatToolLabel\(toolTrace\.toolName/.test(activity),
  },
  {
    name: "activity surface uses the app UI font and quiet Geneva cue, not a terminal prompt card",
    pass:
      /\.activity-panel\s*\{[\s\S]*font-family:\s*var\(--font-ui\)/.test(chat) &&
      /\.activity-geneva-mark/.test(chat) &&
      !/activity-prompt-caret/.test(activity),
  },
  {
    name: "context detail is a readable disclosure panel with labeled rows",
    pass:
      /context-disclosure-panel/.test(bubble) &&
      /function TrustDetail/.test(bubble) &&
      /\.context-disclosure-panel/.test(chat),
  },
  {
    name: "context detail normalizes tools and mode metadata before display",
    pass:
      /formatToolLabel/.test(bubble) &&
      /summary\.mode_label/.test(bubble) &&
      /mode_label/.test(types) &&
      /mode_label/.test(app),
  },
  {
    name: "saved threads restore context disclosure from the context ledger after reload",
    pass:
      /fetchContextLedger/.test(conversation) &&
      /contextSummaryFromLedgerRecord/.test(conversation) &&
      /attachContextSummariesToMessages/.test(conversation),
  },
  {
    name: "live Thinking renders as a Claude-like bare row with Geneva loader before the label",
    pass:
      /\"loader\"/.test(mark) &&
      /geneva-mark-loader-line/.test(mark) &&
      /geneva-mark-loader-large/.test(mark) &&
      /geneva-mark-loader-small/.test(mark) &&
      /activity-thinking-row/.test(activity) &&
      /activityThinkingEvent/.test(activity) &&
      /activityThinkingLabel/.test(activity) &&
      /\.activity-thinking-row/.test(chat) &&
      !/activity-trust-dot/.test(activity) &&
      !/activity-count/.test(activity),
  },
  {
    name: "chat stream does not add a separate status pill under the Claude-like thinking row",
    pass:
      !/StatusLine/.test(canvas) &&
      !/<StatusLine/.test(canvas) &&
      /function statusMarkState/.test(statusLine) &&
      /geneva-mark-loader-thinking/.test(foundation) &&
      /geneva-mark-loader-merging/.test(foundation) &&
      /geneva-mark-loader-responding/.test(foundation),
  },
  {
    name: "answering hides the top Thinking loader so only the bottom response guide remains",
    pass:
      /const hasAssistantContent = message\.content\.trim\(\)\.length > 0/.test(bubble) &&
      /hideLiveThinking=\{hasAssistantContent\}/.test(bubble) &&
      /hideLiveThinking/.test(activity) &&
      /if \(!expanded && !hasProblem && loading && !thinkingEvent\) return null/.test(activity) &&
      /if \(!expanded && !hasProblem && !loading\) return null/.test(activity) &&
      /showResponseGuide/.test(bubble) &&
      /\(hasAssistantContent \|\| !hasLiveThinkingEvent\(activityEvents, Boolean\(message\.loading\)\)\)/.test(bubble) &&
      /assistant-writing-mark/.test(bubble) &&
      /state=\"responding\"/.test(bubble),
  },
  {
    name: "bottom guide is suppressed while the top Thinking loader is active",
    pass:
      /export function hasLiveThinkingEvent/.test(activity) &&
      /const showResponseGuide = Boolean\(message\.loading\) && \(hasAssistantContent \|\| !hasLiveThinkingEvent/.test(bubble),
  },
  {
    name: "live response motion never fades and uses smooth blob morphing instead of circular pulsing",
    pass:
      /\.assistant-writing-mark\s*\{[\s\S]*opacity:\s*1/.test(chat) &&
      /will-change:\s*transform,\s*border-radius/.test(foundation) &&
      /translate3d/.test(foundation) &&
      !hasOpacityInKeyframes(foundation, "geneva-mark-respond") &&
      !hasOpacityInKeyframes(foundation, "geneva-loader-blob-large") &&
      !hasOpacityInKeyframes(foundation, "geneva-loader-blob-small") &&
      !hasOpacityInKeyframes(foundation, "geneva-loader-line-flow"),
  },
  {
    name: "bottom response guide remains a single animated blob below the streaming answer",
    pass:
      /assistant-writing-mark/.test(bubble) &&
      /state=\"responding\"/.test(bubble) &&
      /\.assistant-writing-mark \.geneva-mark-blob/.test(chat),
  },
]

const failed = checks.filter((check) => !check.pass)

if (failed.length) {
  console.error("chat trust layer check failed:")
  for (const check of failed) {
    console.error(`- ${check.name}`)
  }
  process.exit(1)
}

console.log(`chat trust layer check passed (${checks.length} checks)`)
