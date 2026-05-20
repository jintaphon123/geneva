#!/usr/bin/env node

import { readFile } from "node:fs/promises"
import path from "node:path"
import process from "node:process"

const UI_ROOT = path.resolve(import.meta.dirname, "..")

const files = {
  app: path.join(UI_ROOT, "src", "App.tsx"),
  composer: path.join(UI_ROOT, "src", "components", "Composer.tsx"),
  searchOverlay: path.join(UI_ROOT, "src", "components", "SearchOverlay.tsx"),
  types: path.join(UI_ROOT, "src", "types.ts"),
  apiIndex: path.join(UI_ROOT, "src", "lib", "api.ts"),
  searchApi: path.join(UI_ROOT, "src", "lib", "api", "search-api.ts"),
  foundationCss: path.join(UI_ROOT, "src", "styles", "foundation.css"),
  composerCss: path.join(UI_ROOT, "src", "styles", "composer-markdown.css"),
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
  composer,
  searchOverlay,
  types,
  apiIndex,
  searchApi,
  foundationCss,
  composerCss,
] = await Promise.all(Object.values(files).map(safeRead))

const checks = [
  {
    name: "SearchOverlay uses the backend full-brain search API instead of local-only filtering",
    pass:
      /searchGeneva/.test(searchOverlay) &&
      /\/api\/search/.test(searchApi) &&
      /project_id/.test(searchApi) &&
      /types/.test(searchApi) &&
      /from ['"]\.\/api\/search-api['"]/.test(apiIndex),
  },
  {
    name: "UI types model grouped full-brain search results",
    pass:
      /export type SearchResultType/.test(types) &&
      /export type SearchResult/.test(types) &&
      /export type SearchPayload/.test(types) &&
      /research_report/.test(types) &&
      /badges/.test(types),
  },
  {
    name: "Search results are grouped by chats, projects, memories, sources, and research reports",
    pass:
      /Chats/.test(searchOverlay) &&
      /Projects/.test(searchOverlay) &&
      /Memories/.test(searchOverlay) &&
      /Sources/.test(searchOverlay) &&
      /Research reports/.test(searchOverlay) &&
      /SEARCH_TYPE_META/.test(searchOverlay),
  },
  {
    name: "SearchOverlay has real keyboard navigation and active selection",
    pass:
      /activeIndex/.test(searchOverlay) &&
      /ArrowDown/.test(searchOverlay) &&
      /ArrowUp/.test(searchOverlay) &&
      /event\.key === "Enter"/.test(searchOverlay) &&
      /aria-selected/.test(searchOverlay),
  },
  {
    name: "SearchOverlay exposes project-scoped search and useful empty examples",
    pass:
      /scopeProjectOnly/.test(searchOverlay) &&
      /search-scope-row/.test(searchOverlay) &&
      /Search this project/.test(searchOverlay) &&
      /search-empty-examples/.test(searchOverlay) &&
      /Try/.test(searchOverlay),
  },
  {
    name: "SearchOverlay shows result badges and snippets without turning into a hero surface",
    pass:
      /search-result-badge/.test(searchOverlay) &&
      /search-result-snippet/.test(searchOverlay) &&
      /\.search-result-badge/.test(foundationCss) &&
      /\.search-result-snippet/.test(foundationCss) &&
      !/hero/i.test(searchOverlay),
  },
  {
    name: "Global Cmd/Ctrl+K opens SearchOverlay",
    pass:
      /metaKey/.test(app) &&
      /ctrlKey/.test(app) &&
      /setSearchOpen\(true\)/.test(app) &&
      /keydown/.test(app),
  },
  {
    name: "Slash command palette is grouped beyond System and Skills",
    pass:
      /SLASH_COMMAND_GROUPS/.test(composer) &&
      /Project/.test(composer) &&
      /Memory/.test(composer) &&
      /Research/.test(composer) &&
      /Developer/.test(composer) &&
      /Type to filter/.test(composer),
  },
  {
    name: "Slash command search matches names, commands, and descriptions",
    pass:
      /description\.toLowerCase\(\)/.test(composer) &&
      /command\.command\.toLowerCase\(\)/.test(composer) &&
      /includes\(slashQuery\)/.test(composer),
  },
  {
    name: "Slash command palette keeps Claude-like compact hint and keyboard styling",
    pass:
      /\.slash-popup-hint/.test(composerCss) &&
      /\.slash-popup-icon/.test(composerCss) &&
      /\.slash-popup-row\.highlighted/.test(composerCss),
  },
]

const failed = checks.filter((check) => !check.pass)

if (failed.length) {
  console.error("UI-5 search and command center check failed:")
  for (const check of failed) {
    console.error(`- ${check.name}`)
  }
  process.exit(1)
}

console.log(`UI-5 search and command center check passed (${checks.length} checks)`)
