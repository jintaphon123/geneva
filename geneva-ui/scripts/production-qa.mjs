#!/usr/bin/env node

import { spawn } from "node:child_process"
import { mkdir, writeFile } from "node:fs/promises"
import path from "node:path"
import process from "node:process"

const UI_ROOT = path.resolve(import.meta.dirname, "..")
const APP_ROOT = path.resolve(UI_ROOT, "..")
const PYTHON = process.env.PYTHON || "python"
const ARTIFACT_DIR = path.resolve(
  process.env.GENEVA_QA_ARTIFACT_DIR || path.join(UI_ROOT, "test-results", "production-qa"),
)
const REPORT_PATH = path.join(ARTIFACT_DIR, "summary.json")

const checks = [
  {
    name: "frontend lint",
    command: "npm",
    args: ["run", "lint"],
    cwd: UI_ROOT,
  },
  {
    name: "frontend build + static bundle",
    command: "npm",
    args: ["run", "build"],
    cwd: UI_ROOT,
  },
  {
    name: "frontend dependency audit",
    command: "npm",
    args: ["audit", "--omit=dev", "--audit-level=high"],
    cwd: UI_ROOT,
    skip: process.env.GENEVA_QA_SKIP_NPM_AUDIT === "1",
  },
  {
    name: "python dependency audit",
    command: PYTHON,
    args: ["scripts/python-dependency-audit.py"],
    cwd: APP_ROOT,
    skip: process.env.GENEVA_QA_SKIP_PIP_AUDIT === "1",
  },
  {
    name: "production static checks",
    command: "node",
    args: ["scripts/production-static-check.mjs"],
    cwd: UI_ROOT,
  },
  {
    name: "UI-8 responsive production guard",
    command: "npm",
    args: ["run", "check:ui8"],
    cwd: UI_ROOT,
  },
  {
    name: "FastAPI gateway contracts",
    command: PYTHON,
    args: ["scripts/run-fastapi-contracts.py"],
    cwd: APP_ROOT,
  },
  {
    name: "backend skill/service/provider contracts",
    command: PYTHON,
    args: [
      "-m",
      "pytest",
      "tests/test_geneva_skills.py",
      "tests/test_geneva_services.py",
      "tests/test_providers.py",
      "-q",
    ],
    cwd: APP_ROOT,
  },
  {
    name: "desktop/mobile visual smoke",
    command: "npm",
    args: ["run", "visual:smoke"],
    cwd: UI_ROOT,
    skip: process.env.GENEVA_QA_SKIP_VISUAL === "1",
  },
  {
    name: "whitespace diff check",
    command: "git",
    args: [
      "diff",
      "--check",
      "--",
      ".github/workflows",
      "pyproject.toml",
      "requirements.txt",
      "scripts",
      "geneva-ui/package.json",
      "geneva-ui/scripts",
      "geneva-ui/src",
      "geneva-ui/src/index.css",
      "src/geneva",
      "src/geneva/web",
      "tests/test_geneva_web.py",
    ],
    cwd: APP_ROOT,
  },
]

async function main() {
  const startedAt = Date.now()
  const results = []
  let failure = null
  for (const check of checks) {
    if (check.skip) {
      results.push({ name: check.name, status: "skipped", ms: 0 })
      continue
    }
    const checkStartedAt = Date.now()
    try {
      const elapsed = await runCheck(check)
      results.push({ name: check.name, status: "passed", ms: elapsed })
    } catch (error) {
      results.push({
        name: check.name,
        status: "failed",
        ms: Date.now() - checkStartedAt,
        error: error instanceof Error ? error.message : String(error),
      })
      failure = error
      break
    }
  }
  const skipped = results.filter((result) => result.status === "skipped")
  if (!failure && skipped.length > 0) {
    failure = new Error(`Production QA skipped required checks: ${skipped.map((result) => result.name).join(", ")}`)
  }
  const totalMs = Date.now() - startedAt
  printSummary(results, totalMs)
  await writeSummary(results, totalMs, failure)
  if (failure) throw failure
}

function runCheck(check) {
  const startedAt = Date.now()
  console.log(`\n▶ ${check.name}`)
  console.log(`$ ${[check.command, ...check.args].join(" ")}`)
  return new Promise((resolve, reject) => {
    const child = spawn(check.command, check.args, {
      cwd: check.cwd,
      env: { ...process.env, PYTHON },
      stdio: "inherit",
    })
    child.on("error", reject)
    child.on("exit", (code, signal) => {
      const elapsed = Date.now() - startedAt
      if (code === 0) {
        console.log(`✓ ${check.name} passed in ${formatDuration(elapsed)}`)
        resolve(elapsed)
        return
      }
      const suffix = signal ? `signal ${signal}` : `exit ${code}`
      reject(new Error(`${check.name} failed with ${suffix}`))
    })
  })
}

function printSummary(results, totalMs) {
  console.log("\nProduction QA summary")
  for (const result of results) {
    const icon = result.status === "skipped" ? "-" : result.status === "failed" ? "✗" : "✓"
    const timing = result.status === "skipped" ? "skipped" : formatDuration(result.ms)
    console.log(`${icon} ${result.name}: ${timing}`)
    if (result.error) console.log(`  ${result.error}`)
  }
  console.log(`Total: ${formatDuration(totalMs)}`)
  console.log(`Report: ${REPORT_PATH}`)
}

async function writeSummary(results, totalMs, failure) {
  await mkdir(ARTIFACT_DIR, { recursive: true })
  await writeFile(
    REPORT_PATH,
    JSON.stringify(
      {
        ok: !failure,
        generatedAt: new Date().toISOString(),
        totalMs,
        checks: results,
        artifacts: {
          productionSummary: REPORT_PATH,
          ui8Checklist: path.join(UI_ROOT, "docs", "ui8-production-qa-checklist.md"),
          visualSmoke: path.join(UI_ROOT, "test-results", "visual-smoke"),
        },
      },
      null,
      2,
    ),
    "utf8",
  )
}

function formatDuration(ms) {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

await main().catch((error) => {
  console.error(`\nProduction QA failed: ${error.message}`)
  process.exitCode = 1
})
