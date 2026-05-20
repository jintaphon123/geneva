#!/usr/bin/env node

import { readFile } from "node:fs/promises"
import path from "node:path"
import process from "node:process"

const UI_ROOT = path.resolve(import.meta.dirname, "..")

const files = {
  app: path.join(UI_ROOT, "src", "App.tsx"),
  composer: path.join(UI_ROOT, "src", "components", "Composer.tsx"),
  streamApi: path.join(UI_ROOT, "src", "lib", "api", "stream-api.ts"),
}

const [app, composer, streamApi] = await Promise.all(
  Object.values(files).map((file) => readFile(file, "utf8")),
)

const checks = [
  {
    name: "chat stream accepts an AbortSignal and passes it to fetch",
    pass:
      /signal\?:\s*AbortSignal/.test(streamApi) &&
      /signal:\s*payload\.signal/.test(streamApi),
  },
  {
    name: "chat stream exposes session_id from early SSE events, not only turn_complete",
    pass:
      /const sessionId = event\.data\?\.session_id/.test(streamApi) &&
      !/if \(event\.type === "turn_complete"\)\s*\{[\s\S]*callbacks\.onSession/.test(streamApi),
  },
  {
    name: "App owns an AbortController for the active chat request",
    pass:
      /activeChatAbortRef/.test(app) &&
      /new AbortController\(\)/.test(app) &&
      /signal:\s*abortController\.signal/.test(app),
  },
  {
    name: "Stop aborts the active fetch immediately before asking backend to cancel",
    pass:
      /activeChatAbortRef\.current\?\.abort\(\)/.test(app) &&
      /currentStreamSessionIdRef\.current\s*\?\? sessionId/.test(app),
  },
  {
    name: "AbortError is treated as an intentional stop, not a chat failure",
    pass:
      /isAbortError/.test(app) &&
      /if \(isAbortError\(error\)\)/.test(app),
  },
  {
    name: "turn_complete clears live loading state immediately",
    pass:
      /event\.type === "turn_complete"[\s\S]*setLoading\(false\)[\s\S]*setStatusText\(null\)/.test(app),
  },
  {
    name: "post-answer refresh is fire-and-forget so the composer unlocks fast",
    pass:
      /void Promise\.all\(\[refreshMemory\(\), refreshSessions\(\), refreshProjects\(\)\]\)/.test(app) &&
      !/await Promise\.all\(\[refreshMemory\(\), refreshSessions\(\), refreshProjects\(\)\]\)/.test(app),
  },
  {
    name: "Composer keeps a dedicated stop button for loading turns",
    pass:
      /aria-label="Stop generation"/.test(composer) &&
      /onClick=\{onStop\}/.test(composer),
  },
]

const failed = checks.filter((check) => !check.pass)

if (failed.length) {
  console.error("chat cancel/performance check failed:")
  for (const check of failed) {
    console.error(`- ${check.name}`)
  }
  process.exit(1)
}

console.log(`chat cancel/performance check passed (${checks.length} checks)`)
