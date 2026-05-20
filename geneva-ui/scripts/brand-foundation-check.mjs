#!/usr/bin/env node

import { readFile } from "node:fs/promises"
import path from "node:path"
import process from "node:process"

const UI_ROOT = path.resolve(import.meta.dirname, "..")

const files = {
  mark: path.join(UI_ROOT, "src", "components", "GenevaMark.tsx"),
  foundation: path.join(UI_ROOT, "src", "styles", "foundation.css"),
  chat: path.join(UI_ROOT, "src", "styles", "chat.css"),
  theme: path.join(UI_ROOT, "src", "lib", "theme.ts"),
}

const [mark, foundation, chat, theme] = await Promise.all(
  Object.values(files).map((file) => readFile(file, "utf8")),
)

const checks = [
  {
    name: "theme defaults to light unless the user explicitly changes it",
    pass: /return "light"/.test(theme) && !/return "system"\s*\n?\}/.test(theme),
  },
  {
    name: "theme has a user-set sentinel so System can remain an explicit choice",
    pass: /THEME_MODE_USER_SET_KEY/.test(theme),
  },
  {
    name: "Geneva mark includes the merge state between thinking and responding",
    pass: /"merging"/.test(mark) && /GenevaMarkState/.test(mark),
  },
  {
    name: "Geneva mark uses locked brand anatomy and full standalone viewBox",
    pass:
      /viewBox="0 0 110 28"/.test(mark) &&
      /x2="88"/.test(mark) &&
      /cx="98"/.test(mark),
  },
  {
    name: "sidebar wordmark follows brand guideline weight and spacing",
    pass:
      /\.sidebar-brand\s*\{[\s\S]*font-weight:\s*500/.test(foundation) &&
      /\.sidebar-brand\s*\{[\s\S]*letter-spacing:\s*0\.01em/.test(foundation),
  },
  {
    name: "brand motion has reduced-motion fallback",
    pass: /prefers-reduced-motion:\s*reduce/.test(foundation) && /geneva-mark/.test(foundation),
  },
  {
    name: "responding state is available as a below-message brand indicator",
    pass: /assistant-writing-mark/.test(chat),
  },
]

const failed = checks.filter((check) => !check.pass)

if (failed.length) {
  console.error("brand foundation check failed:")
  for (const check of failed) {
    console.error(`- ${check.name}`)
  }
  process.exit(1)
}

console.log(`brand foundation check passed (${checks.length} checks)`)
