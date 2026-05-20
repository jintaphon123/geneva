#!/usr/bin/env node

import { spawn } from "node:child_process"
import net from "node:net"
import path from "node:path"
import process from "node:process"

const UI_ROOT = path.resolve(import.meta.dirname, "..")
const APP_ROOT = path.resolve(UI_ROOT, "..")
const PYTHON = process.env.PYTHON || "python"
const API_HOST = process.env.GENEVA_WEB_HOST || "127.0.0.1"
const API_PORT = Number(process.env.GENEVA_WEB_PORT || "8765")

const children = new Set()
let shuttingDown = false

async function main() {
  if (!(await isPortOpen(API_HOST, API_PORT))) {
    const api = spawn(
      PYTHON,
      ["-m", "src.geneva.web_server", "--host", API_HOST, "--port", String(API_PORT)],
      {
        cwd: APP_ROOT,
        env: { ...process.env, PYTHONUNBUFFERED: "1" },
        stdio: ["ignore", "pipe", "pipe"],
      },
    )
    track(api, "api")
    await waitForApi(api)
  } else {
    console.log(`[api] using existing Geneva backend at http://${API_HOST}:${API_PORT}`)
  }

  const vite = spawn("vite", process.argv.slice(2), {
    cwd: UI_ROOT,
    env: process.env,
    stdio: ["ignore", "pipe", "pipe"],
  })
  track(vite, "vite")
}

function track(child, label) {
  children.add(child)
  child.stdout?.on("data", (chunk) => writeLog(label, chunk))
  child.stderr?.on("data", (chunk) => writeLog(label, chunk))
  child.on("exit", (code, signal) => {
    children.delete(child)
    if (shuttingDown) return
    if (label === "api") {
      console.error(`[api] exited before the dev UI stopped (${formatExit(code, signal)})`)
      shutdown(1)
      return
    }
    shutdown(code ?? 0)
  })
}

function writeLog(label, chunk) {
  for (const line of String(chunk).split(/\r?\n/)) {
    if (line.trim()) console.log(`[${label}] ${line}`)
  }
}

function formatExit(code, signal) {
  return signal ? `signal ${signal}` : `code ${code ?? 0}`
}

async function waitForApi(child) {
  const started = Date.now()
  while (Date.now() - started < 15_000) {
    if (child.exitCode !== null) {
      throw new Error(`Geneva backend exited early with code ${child.exitCode}`)
    }
    if (await isPortOpen(API_HOST, API_PORT)) {
      console.log(`[api] ready at http://${API_HOST}:${API_PORT}`)
      return
    }
    await delay(200)
  }
  throw new Error(`Timed out waiting for Geneva backend at ${API_HOST}:${API_PORT}`)
}

function isPortOpen(host, port) {
  return new Promise((resolve) => {
    const socket = net.connect({ host, port })
    socket.setTimeout(500)
    socket.once("connect", () => {
      socket.destroy()
      resolve(true)
    })
    socket.once("timeout", () => {
      socket.destroy()
      resolve(false)
    })
    socket.once("error", () => resolve(false))
  })
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function shutdown(code = 0) {
  if (shuttingDown) return
  shuttingDown = true
  for (const child of children) {
    child.kill("SIGTERM")
  }
  setTimeout(() => process.exit(code), 200).unref()
}

process.once("SIGINT", () => shutdown(0))
process.once("SIGTERM", () => shutdown(0))

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error))
  shutdown(1)
})
