#!/usr/bin/env node

import { spawn } from "node:child_process"
import { createHash } from "node:crypto"
import { createServer } from "node:net"
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises"
import { homedir, tmpdir } from "node:os"
import path from "node:path"
import process from "node:process"

const UI_ROOT = path.resolve(import.meta.dirname, "..")
const APP_ROOT = path.resolve(UI_ROOT, "..")
const RESULT_DIR = path.resolve(UI_ROOT, "test-results", "visual-smoke")
const CHROME_CANDIDATES = [
  process.env.CHROME_BIN,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/usr/bin/google-chrome",
  "/usr/bin/google-chrome-stable",
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser",
].filter(Boolean)

const SESSION_ID = `visual_smoke_${Date.now()}`
const LEDGER_PATH = path.join(homedir(), ".geneva", "context-ledger", `${safeSessionId(SESSION_ID)}.jsonl`)
const SESSION_PATH = path.join(homedir(), ".geneva", "sessions", `${SESSION_ID}.json`)
const PYTHON = process.env.PYTHON || "python"
const JSON_MUTATION_HEADERS = {
  "Content-Type": "application/json",
  "X-Second-Brain-Request": "1",
}

let webServer
let chrome
let brainDbDir
let chromeProfile
let skillsDir

async function main() {
  try {
    await mkdir(path.dirname(LEDGER_PATH), { recursive: true })
    await mkdir(path.dirname(SESSION_PATH), { recursive: true })
    await mkdir(RESULT_DIR, { recursive: true })
    await writeFile(LEDGER_PATH, JSON.stringify(buildLedgerFixture()) + "\n", "utf8")
    await writeFile(SESSION_PATH, JSON.stringify(buildSessionFixture(), null, 2), "utf8")
    brainDbDir = await mkdtemp(path.join(tmpdir(), "geneva-db-"))
    skillsDir = await mkdtemp(path.join(tmpdir(), "geneva-skills-"))
    const memoryEventsDir = path.join(brainDbDir, "events")
    await mkdir(memoryEventsDir, { recursive: true })

    const appPort = await freePort()
    const cdpPort = await freePort()
    webServer = spawn(PYTHON, ["-m", "src.geneva.web_server", "--host", "127.0.0.1", "--port", String(appPort)], {
      cwd: APP_ROOT,
      env: {
        ...process.env,
        GENEVA_BRAIN_DB_PATH: path.join(brainDbDir, "brain.db"),
        GENEVA_MEMORY_EVENTS_DIR: memoryEventsDir,
        PYTHONUNBUFFERED: "1",
        GENEVA_SKILLS_DIR: skillsDir,
      },
      stdio: ["ignore", "pipe", "pipe"],
    })
    const serverLog = captureProcessLog(webServer, "web")
    await waitForHttp(`http://127.0.0.1:${appPort}/`, 15_000, serverLog)
    await seedSkillFixture(appPort)
    await seedProjectFixture(appPort)
    await assertContextCommand(appPort)

    const chromeBin = await findChrome()
    chromeProfile = await mkdtemp(path.join(tmpdir(), "geneva-visual-smoke-"))
    chrome = spawn(
      chromeBin,
      [
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        `--remote-debugging-port=${cdpPort}`,
        `--user-data-dir=${chromeProfile}`,
        "about:blank",
      ],
      { stdio: ["ignore", "pipe", "pipe"] },
    )
    const chromeLog = captureProcessLog(chrome, "chrome")
    await waitForHttp(`http://127.0.0.1:${cdpPort}/json/version`, 15_000, chromeLog)

    const page = await openCdpPage(cdpPort)
    const url = `http://127.0.0.1:${appPort}/`
    await smokeViewport(page, {
      appPort,
      cdpPort,
      height: 900,
      mobile: false,
      name: "desktop-dark",
      themeMode: "dark",
      url,
      width: 1440,
    })
    await smokeViewport(page, {
      appPort,
      cdpPort,
      height: 900,
      mobile: false,
      name: "desktop-light",
      themeMode: "light",
      url,
      width: 1440,
    })
    await smokeViewport(page, {
      appPort,
      cdpPort,
      height: 812,
      mobile: true,
      name: "mobile-dark",
      themeMode: "dark",
      url,
      width: 375,
    })

    console.log(`visual smoke passed: ${RESULT_DIR}`)
  } finally {
    await terminateProcess(chrome)
    await terminateProcess(webServer)
    await safeRm(chromeProfile, { recursive: true, force: true })
    await safeRm(brainDbDir, { recursive: true, force: true })
    await safeRm(skillsDir, { recursive: true, force: true })
    await safeRm(LEDGER_PATH, { force: true })
    await safeRm(SESSION_PATH, { force: true })
  }
}

async function smokeViewport(page, options) {
  const errors = []
  page.on("event", (message) => {
    if (message.method === "Runtime.exceptionThrown") {
      errors.push(message.params.exceptionDetails?.text || "Runtime exception")
    }
    if (message.method === "Log.entryAdded" && message.params.entry?.level === "error") {
      errors.push(message.params.entry.text || "Console error")
    }
  })
  await page.send("Runtime.enable")
  await page.send("Log.enable")
  await page.send("Page.enable")
  await page.send("Emulation.setDeviceMetricsOverride", {
    width: options.width,
    height: options.height,
    deviceScaleFactor: 1,
    mobile: options.mobile,
  })
  await page.send("Page.navigate", { url: options.url })
  await waitForReady(page)
  await page.evaluate(`(() => {
    localStorage.setItem("geneva.activeSessionId", ${JSON.stringify(SESSION_ID)});
    localStorage.setItem("geneva.themeMode", ${JSON.stringify(options.themeMode || "system")});
    localStorage.setItem("geneva.themeModeUserSet", "1");
  })()`)
  await page.send("Page.navigate", { url: options.url })
  await waitForReady(page)
  await delay(250)

  const metrics = await page.evaluate(`(() => {
    return {
      innerWidth,
      innerHeight,
      scrollWidth: document.documentElement.scrollWidth,
      themeMode: localStorage.getItem("geneva.themeMode"),
      themeDataset: document.documentElement.dataset.themeMode,
      isDark: document.documentElement.classList.contains("dark"),
      hasSettingsButton: Boolean(document.querySelector('button[aria-label="Open settings"]')),
      hasOpenSourceEntry: Boolean(document.querySelector(".sidebar-open-source-action")),
      hasContextButton: Boolean(document.querySelector('[aria-label="Toggle context inspector"]')),
      hasGhostButton: Boolean(document.querySelector('[aria-label="Toggle ghost mode"]')),
      hasMemoryButton: Boolean(document.querySelector('[aria-label="Toggle memory panel"]')),
      hasActivityPanel: Boolean(document.querySelector(".activity-panel")),
      hasActivityCopy: (document.body.innerText || "").includes("Finished Read"),
      visibleProjectRows: document.querySelectorAll(".project-item").length,
      hasProjectCount: Boolean(document.querySelector(".project-list-count")),
      projectCount: Number.parseInt(document.querySelector(".project-list-count")?.textContent || "0", 10),
      hasProjectPagination: Boolean(document.querySelector(".project-see-all")),
      hasEmptyVoiceButton: Boolean(document.querySelector('button[aria-label="Voice input"]')),
      hasEmptySendButton: Boolean(document.querySelector('button[aria-label="Send message"]')),
      actionRows: document.querySelectorAll(".message-action-row").length,
      hasRetryAction: Boolean(document.querySelector('button[aria-label="Retry response"]')),
      hasForkAction: Boolean(document.querySelector('button[aria-label="Fork from here"]')),
      markdownFontSize: Number.parseFloat(getComputedStyle(document.querySelector(".markdown-body") || document.body).fontSize),
      scrollViewportOverscroll: getComputedStyle(document.querySelector(".chat-scroll [data-scroll-viewport]") || document.body).overscrollBehaviorY,
    };
  })()`)

  assert(!metrics.hasContextButton, `${options.name}: context inspector button should not be visible`)
  assert(metrics.themeMode === (options.themeMode || "system"), `${options.name}: theme mode did not persist`)
  assert(metrics.themeDataset === (options.themeMode || "system"), `${options.name}: theme mode dataset is stale`)
  if (options.themeMode === "dark") assert(metrics.isDark, `${options.name}: dark theme class missing`)
  if (options.themeMode === "light") assert(!metrics.isDark, `${options.name}: light theme should not have dark class`)
  assert(metrics.hasSettingsButton, `${options.name}: settings button is missing`)
  assert(metrics.hasOpenSourceEntry, `${options.name}: open source entry is missing`)
  assert(metrics.hasGhostButton, `${options.name}: missing ghost mode button`)
  assert(!metrics.hasMemoryButton, `${options.name}: memory/context panel button should be removed; use /context instead`)
  assert(metrics.hasActivityPanel, `${options.name}: restored run activity should render in chat history`)
  assert(metrics.hasActivityCopy, `${options.name}: activity panel should summarize restored tool work`)
  assert(metrics.hasProjectCount, `${options.name}: project list count is missing`)
  assert(metrics.projectCount >= 30, `${options.name}: project fixture count is too small (${metrics.projectCount})`)
  assert(metrics.hasProjectPagination, `${options.name}: project list should paginate large project sets`)
  assert(metrics.visibleProjectRows <= 6, `${options.name}: sidebar rendered too many projects initially (${metrics.visibleProjectRows})`)
  assert(metrics.hasEmptyVoiceButton, `${options.name}: empty composer should show the voice button`)
  assert(!metrics.hasEmptySendButton, `${options.name}: empty composer should not show a send button`)
  assert(metrics.actionRows >= 2, `${options.name}: message actions should render on chat messages`)
  assert(metrics.hasRetryAction, `${options.name}: assistant retry action is missing`)
  assert(metrics.hasForkAction, `${options.name}: fork action is missing`)
  assert(metrics.markdownFontSize <= 14.5, `${options.name}: markdown text is too large at ${metrics.markdownFontSize}px`)
  assert(metrics.scrollViewportOverscroll !== "auto", `${options.name}: chat scroll viewport should contain overscroll`)
  assert(metrics.scrollWidth <= metrics.innerWidth, `${options.name}: horizontal overflow ${metrics.scrollWidth} > ${metrics.innerWidth}`)
  assert(blockingPageErrors(errors).length === 0, `${options.name}: console/runtime errors\n${blockingPageErrors(errors).join("\n")}`)

  const ui8MobileMetrics = await page.evaluate(`(() => ({
    innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
    hasMobileSidebarTrigger: Boolean(document.querySelector(".mobile-sidebar-trigger")),
    hasComposerOverflowContract: Boolean(document.querySelector(".composer-active-pills")) || Boolean(document.querySelector(".composer-box")),
    bodyOverflowX: getComputedStyle(document.body).overflowX,
    rootOverflowX: getComputedStyle(document.documentElement).overflowX,
  }))()`)
  assert(
    ui8MobileMetrics.scrollWidth <= ui8MobileMetrics.innerWidth,
    `${options.name}: UI-8 horizontal overflow ${ui8MobileMetrics.scrollWidth} > ${ui8MobileMetrics.innerWidth}`,
  )
  if (options.mobile) {
    assert(ui8MobileMetrics.hasMobileSidebarTrigger, `${options.name}: UI-8 mobile sidebar trigger is missing`)
    assert(ui8MobileMetrics.bodyOverflowX === "hidden", `${options.name}: UI-8 mobile body should hide horizontal overflow`)
    assert(ui8MobileMetrics.rootOverflowX === "hidden", `${options.name}: UI-8 mobile root should hide horizontal overflow`)
  }

  await page.evaluate(`(() => {
    const trigger = document.querySelector('button[aria-label="Open settings"]');
    if (!(trigger instanceof HTMLButtonElement)) throw new Error("Settings button missing");
    trigger.click();
  })()`)
  await waitForPageCondition(
    page,
    'document.querySelector(".settings-page")',
    5_000,
    `${options.name}: settings did not open`,
  )
  const themeMenuMetrics = await page.evaluate(`(() => ({
    hasSettings: Boolean(document.querySelector(".settings-page")),
    selectedCount: document.querySelectorAll('.settings-appearance-options button[aria-checked="true"]').length,
    hasSystem: Array.from(document.querySelectorAll(".settings-appearance-options strong")).some((item) => item.textContent === "System"),
    hasLight: Array.from(document.querySelectorAll(".settings-appearance-options strong")).some((item) => item.textContent === "Light"),
    hasDark: Array.from(document.querySelectorAll(".settings-appearance-options strong")).some((item) => item.textContent === "Dark"),
  }))()`)
  assert(themeMenuMetrics.hasSettings, `${options.name}: settings did not open`)
  assert(themeMenuMetrics.selectedCount === 1, `${options.name}: appearance settings should have exactly one selected option`)
  assert(themeMenuMetrics.hasSystem, `${options.name}: appearance settings missing System option`)
  assert(themeMenuMetrics.hasLight, `${options.name}: appearance settings missing Light option`)
  assert(themeMenuMetrics.hasDark, `${options.name}: appearance settings missing Dark option`)
  await page.evaluate(`(() => {
    const button = Array.from(document.querySelectorAll(".settings-appearance-options button")).find((item) => item.textContent?.includes("${themeOptionLabel(options.themeMode || "system")}"));
    if (!(button instanceof HTMLButtonElement)) throw new Error("Current theme option missing");
    button.click();
    const back = document.querySelector(".settings-back");
    if (!(back instanceof HTMLButtonElement)) throw new Error("Settings back missing");
    back.click();
  })()`)
  await delay(150)

  await page.evaluate(`(() => {
    const viewport = document.querySelector(".chat-scroll [data-scroll-viewport]");
    if (!(viewport instanceof HTMLElement)) throw new Error("Scroll viewport missing");
    window.scrollTo(0, 0);
    viewport.scrollTop = 0;
    viewport.dispatchEvent(new Event("scroll", { bubbles: true }));
  })()`)
  await delay(150)
  const scrollStability = await page.evaluate(`(() => ({
    hasJumpButton: Boolean(document.querySelector(".jump-to-latest")),
    windowScrollY: window.scrollY,
    bodyScrollTop: document.scrollingElement?.scrollTop ?? 0,
  }))()`)
  assert(scrollStability.hasJumpButton, `${options.name}: jump-to-latest should appear when user scrolls away from bottom`)
  assert(scrollStability.windowScrollY === 0, `${options.name}: window scrolled instead of chat viewport`)
  assert(scrollStability.bodyScrollTop === 0, `${options.name}: document scrolled instead of chat viewport`)

  await page.evaluate(`(() => {
    const textarea = document.querySelector('textarea[aria-label="Message"]');
    if (!(textarea instanceof HTMLTextAreaElement)) throw new Error("Message textarea missing");
    const valueSetter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")?.set;
    valueSetter?.call(textarea, "composer transition check");
    textarea.dispatchEvent(new Event("input", { bubbles: true }));
  })()`)
  await delay(150)
  const composerMetrics = await page.evaluate(`(() => ({
    hasTypedVoiceButton: Boolean(document.querySelector('button[aria-label="Voice input"]')),
    hasTypedSendButton: Boolean(document.querySelector('button[aria-label="Send message"]')),
    composerHeight: document.querySelector(".composer-box")?.getBoundingClientRect().height ?? 0,
  }))()`)
  assert(!composerMetrics.hasTypedVoiceButton, `${options.name}: typed composer should hide the voice button`)
  assert(composerMetrics.hasTypedSendButton, `${options.name}: typed composer should show the send button`)
  assert(composerMetrics.composerHeight <= 96, `${options.name}: composer is too tall at ${composerMetrics.composerHeight}px`)

  const chatScreenshot = await page.send("Page.captureScreenshot", { format: "png", fromSurface: true })
  await writeFile(path.join(RESULT_DIR, `${options.name}.png`), Buffer.from(chatScreenshot.data, "base64"))

  await page.evaluate(`(() => {
    const closeMemory = document.querySelector('button[aria-label="Hide memory"]');
    if (closeMemory instanceof HTMLButtonElement) closeMemory.click();
  })()`)
  await delay(250)

  if (options.mobile) {
    await page.evaluate(`(() => {
      const mobileTrigger = document.querySelector(".mobile-sidebar-trigger");
      const sidebar = document.querySelector(".app-sidebar");
      if (mobileTrigger instanceof HTMLButtonElement && !sidebar?.classList.contains("mobile-open")) {
        mobileTrigger.click();
      }
    })()`)
    await delay(200)
  }
  await page.evaluate(`(() => {
    const button = document.querySelector(".sidebar-open-source-action");
    if (!(button instanceof HTMLButtonElement)) throw new Error("Open Source sidebar action missing");
    button.click();
  })()`)
  await delay(300)
  const openSourceMetrics = await page.evaluate(`(() => {
    const text = document.body.innerText || "";
    return {
      hasModal: Boolean(document.querySelector(".open-source-panel")),
      modalRole: document.querySelector(".open-source-panel")?.getAttribute("role") || "",
      ariaModal: document.querySelector(".open-source-panel")?.getAttribute("aria-modal") || "",
      hasFlow: Boolean(document.querySelector(".open-source-flow")),
      metricCount: document.querySelectorAll(".open-source-metric").length,
      hasGovernance: Boolean(document.querySelector(".open-source-governance")),
      hasFooterAction: Boolean(document.querySelector(".open-source-footer button")),
      hasReviewQueue: text.includes("Review queue"),
      hasReuseIndex: text.includes("Reuse index"),
      hasPublishContract: text.includes("Publish contract"),
      hasSearchFirst: text.includes("Search first"),
      hasOverlayClosed: !document.querySelector(".app-sidebar")?.classList.contains("mobile-open"),
      innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
    };
  })()`)
  assert(openSourceMetrics.hasModal, `${options.name}: Open Source modal did not open`)
  assert(openSourceMetrics.modalRole === "dialog", `${options.name}: Open Source modal must use role=dialog`)
  assert(openSourceMetrics.ariaModal === "true", `${options.name}: Open Source modal must be aria-modal`)
  assert(openSourceMetrics.hasFlow, `${options.name}: Open Source pipeline is missing`)
  assert(openSourceMetrics.metricCount >= 4, `${options.name}: Open Source readiness metrics are missing`)
  assert(openSourceMetrics.hasGovernance, `${options.name}: Open Source publish governance is missing`)
  assert(openSourceMetrics.hasFooterAction, `${options.name}: Open Source footer action is missing`)
  assert(openSourceMetrics.hasReviewQueue, `${options.name}: Open Source review queue copy is missing`)
  assert(openSourceMetrics.hasReuseIndex, `${options.name}: Open Source reuse index copy is missing`)
  assert(openSourceMetrics.hasPublishContract, `${options.name}: Open Source publish contract is missing`)
  assert(openSourceMetrics.hasSearchFirst, `${options.name}: Open Source search-first policy is missing`)
  if (options.mobile) assert(openSourceMetrics.hasOverlayClosed, `${options.name}: mobile sidebar stayed open after Open Source action`)
  assert(openSourceMetrics.scrollWidth <= openSourceMetrics.innerWidth, `${options.name}: Open Source caused horizontal overflow`)
  const openSourceScreenshot = await page.send("Page.captureScreenshot", { format: "png", fromSurface: true })
  await writeFile(path.join(RESULT_DIR, `${options.name}-open-source.png`), Buffer.from(openSourceScreenshot.data, "base64"))
  await page.evaluate(`(() => {
    const close = document.querySelector('button[aria-label="Close Library"], button[aria-label="Close Open Source"]');
    if (close instanceof HTMLButtonElement) close.click();
  })()`)
  await delay(250)

  if (options.mobile) {
    await page.evaluate(`(() => {
      const mobileTrigger = document.querySelector(".mobile-sidebar-trigger");
      const sidebar = document.querySelector(".app-sidebar");
      if (mobileTrigger instanceof HTMLButtonElement && !sidebar?.classList.contains("mobile-open")) {
        mobileTrigger.click();
      }
    })()`)
    await delay(200)
  }
  await page.evaluate(`(() => {
    const skillTab = document.querySelector('button[aria-label="Customize"], button[title="Customize"], .sidebar-skills-action, button[title="Skills"]');
    if (!(skillTab instanceof HTMLButtonElement)) throw new Error("Customize sidebar action missing");
    skillTab.click();
  })()`)
  await waitForPageCondition(
    page,
    'document.querySelector(".customize-surface")',
    5_000,
    `${options.name}: customize surface did not render`,
  )
  await page.evaluate(`(() => {
    const skills = [...document.querySelectorAll(".customize-overview-row, .customize-nav button")]
      .find((candidate) => (candidate.textContent || "").includes("Skills"));
    if (skills instanceof HTMLButtonElement) skills.click();
  })()`)
  await waitForPageCondition(
    page,
    'document.querySelector(".skill-browser")',
    5_000,
    `${options.name}: skill browser did not render`,
  )
  await page.evaluate(`(() => {
    const installed = [...document.querySelectorAll(".skill-filter-button")]
      .find((candidate) => (candidate.textContent || "").includes("Installed"));
    if (installed instanceof HTMLButtonElement) installed.click();
  })()`)
  await waitForPageCondition(
    page,
    'document.querySelectorAll(".skill-list-row").length > 0',
    5_000,
    `${options.name}: skill list rows did not render`,
  )
  const skillMetrics = await page.evaluate(`(() => {
    const text = document.body.innerText || "";
    return {
      innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      hasSkillBrowser: Boolean(document.querySelector(".skill-browser")),
      hasCustomizeTopbar: Boolean(document.querySelector(".skill-customize-topbar")),
      filterButtons: document.querySelectorAll(".skill-filter-button").length,
      hasRecommendationStrip: Boolean(document.querySelector(".skill-recommendation-strip")),
      hasSkillSearch: Boolean(document.querySelector(".skill-main-search")),
      hasAddSkillButton: Boolean(document.querySelector('button[aria-label="Add skill"]')),
      skillRows: document.querySelectorAll(".skill-list-row").length,
      hasNeedsReviewFilter: text.includes("Needs review"),
    };
  })()`)
  assert(skillMetrics.hasSkillBrowser, `${options.name}: skill browser did not render`)
  assert(skillMetrics.hasCustomizeTopbar, `${options.name}: skill customize topbar did not render`)
  assert(skillMetrics.filterButtons >= 6, `${options.name}: skill filter rail is incomplete`)
  assert(skillMetrics.hasRecommendationStrip, `${options.name}: skill recommendation strip is missing`)
  assert(skillMetrics.hasSkillSearch, `${options.name}: skill search is missing`)
  assert(skillMetrics.hasAddSkillButton, `${options.name}: skill add menu is missing`)
  assert(skillMetrics.hasNeedsReviewFilter, `${options.name}: skill review filter copy is missing`)
  assert(skillMetrics.skillRows >= 10, `${options.name}: skill list should survive a larger fixture (${skillMetrics.skillRows} rows)`)
  assert(skillMetrics.scrollWidth <= skillMetrics.innerWidth, `${options.name}: skill view horizontal overflow ${skillMetrics.scrollWidth} > ${skillMetrics.innerWidth}`)
  assert(
    blockingPageErrors(errors).length === 0,
    `${options.name}: console/runtime errors after skill view\n${blockingPageErrors(errors).join("\n")}`,
  )

  await page.evaluate(`(() => {
    const review = [...document.querySelectorAll(".skill-filter-button")]
      .find((candidate) => (candidate.textContent || "").includes("Needs review"));
    if (review instanceof HTMLButtonElement) review.click();
  })()`)
  await waitForPageCondition(
    page,
    '[...document.querySelectorAll(".skill-list-row")].some((candidate) => (candidate.textContent || "").includes("visual-review"))',
    5_000,
    `${options.name}: seeded review skill missing`,
  )
  await page.evaluate(`(() => {
    const row = [...document.querySelectorAll(".skill-list-row")]
      .find((candidate) => (candidate.textContent || "").includes("visual-review"));
    const menu = row?.querySelector(".skill-card-menu");
    if (!(menu instanceof HTMLButtonElement)) throw new Error("Skill options menu missing");
    menu.click();
  })()`)
  await delay(150)
  await page.evaluate(`(() => {
    const button = [...document.querySelectorAll(".skill-card-popover button")]
      .find((candidate) => (candidate.textContent || "").includes("Delete"));
    if (!(button instanceof HTMLButtonElement)) throw new Error("Skill delete action missing");
    button.click();
  })()`)
  await delay(150)
  const skillDeleteMetrics = await page.evaluate(`(() => {
    const text = document.body.innerText || "";
    return {
      hasDeleteModal: text.includes("Delete skill?"),
      hasPersistenceCopy: text.includes("slash commands after the next sync"),
      hasCloseButton: Boolean(document.querySelector('button[aria-label="Close delete skill confirmation"]')),
    };
  })()`)
  assert(skillDeleteMetrics.hasDeleteModal, `${options.name}: skill delete confirmation did not open`)
  assert(skillDeleteMetrics.hasPersistenceCopy, `${options.name}: skill delete confirmation lacks persistence copy`)
  assert(skillDeleteMetrics.hasCloseButton, `${options.name}: skill delete confirmation lacks close button`)
  await page.evaluate(`(() => {
    const close = document.querySelector('button[aria-label="Close delete skill confirmation"]');
    if (close instanceof HTMLButtonElement) close.click();
  })()`)
  await delay(150)

  const skillScreenshot = await page.send("Page.captureScreenshot", { format: "png", fromSurface: true })
  await writeFile(path.join(RESULT_DIR, `${options.name}-skills.png`), Buffer.from(skillScreenshot.data, "base64"))

  await page.send("Page.navigate", { url: options.url })
  await waitForReady(page)
  await page.evaluate(`(() => {
    localStorage.setItem("geneva.activeSessionId", ${JSON.stringify(SESSION_ID)});
    localStorage.setItem("geneva.themeMode", ${JSON.stringify(options.themeMode || "system")});
    localStorage.setItem("geneva.themeModeUserSet", "1");
  })()`)
  await page.send("Page.navigate", { url: options.url })
  await waitForReady(page)
  await delay(350)

  if (options.mobile) {
    await page.evaluate(`(() => {
      const mobileTrigger = document.querySelector(".mobile-sidebar-trigger");
      if (mobileTrigger instanceof HTMLButtonElement) mobileTrigger.click();
    })()`)
    await delay(200)
  }
  await page.evaluate(`(() => {
    const row = [...document.querySelectorAll(".project-item")]
      .find((candidate) => (candidate.textContent || "").includes("Visual Smoke Project"));
    const button = row?.querySelector(".project-main-button");
    if (!(button instanceof HTMLButtonElement)) throw new Error("Seeded project button missing");
    button.click();
  })()`)
  await waitForPageCondition(
    page,
    'document.querySelector(".project-view")',
    5_000,
    `${options.name}: project view did not render after project click`,
  )
  await delay(250)
  let projectContextSheetOpen = false
  if (options.mobile) {
    await page.evaluate(`(() => {
      const toggle = document.querySelector(".project-mobile-context-toggle");
      if (!(toggle instanceof HTMLButtonElement)) throw new Error("Project context mobile toggle missing");
      toggle.click();
    })()`)
    await delay(250)
    projectContextSheetOpen = await page.evaluate(`Boolean(document.querySelector(".project-context-mobile-sheet.open"))`)
    assert(projectContextSheetOpen, `${options.name}: project context bottom sheet did not open`)
    const sheetScreenshot = await page.send("Page.captureScreenshot", { format: "png", fromSurface: true })
    await writeFile(path.join(RESULT_DIR, `${options.name}-project-context-sheet.png`), Buffer.from(sheetScreenshot.data, "base64"))
  }
  const projectMetrics = await page.evaluate(`(() => {
    const text = document.body.innerText || "";
    const rail = document.querySelector(".project-command-rail");
    const composer = document.querySelector(".project-launch-composer");
    const title = document.querySelector(".project-view-title")?.getBoundingClientRect();
    const actions = document.querySelector(".project-header-actions")?.getBoundingClientRect();
    return {
      hasProjectView: Boolean(document.querySelector(".project-view")),
      hasCommandRail: Boolean(rail),
      hasProjectPlanList: Boolean(document.querySelector(".project-plan-list")),
      hasNextStep: Boolean(document.querySelector(".project-next-step-card")),
      hasRunPreview: Boolean(document.querySelector(".project-run-preview")),
      hasWorkspaceStatus: Boolean(document.querySelector(".project-state-line")),
      hasPlanStatuses: document.querySelectorAll(".project-plan-status").length >= 2,
      hasAgentHarnessEntry: Boolean(document.querySelector(".project-cowork-entry")),
      hasMemoryCapture: Boolean(document.querySelector(".project-memory-capture")),
      hasSeededMemory: text.includes("Visual smoke project memory should appear"),
      hasSeededTodo: text.includes("Wire agent-harness progress into project chats"),
      hasProjectContextToggle: Boolean(document.querySelector(".project-mobile-context-toggle")),
      projectContextSheetOpen: Boolean(document.querySelector(".project-context-mobile-sheet.open")),
      sidebarOpen: Boolean(document.querySelector(".app-sidebar.mobile-open")),
      composerHeight: composer?.getBoundingClientRect().height ?? 0,
      headerHasRoom: !title || !actions || title.right + 8 <= actions.left,
      headerClearsMobileTrigger: !title || title.left >= 50,
      railWidth: rail?.getBoundingClientRect().width ?? 0,
      innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
    };
  })()`)
  assert(projectMetrics.hasProjectView, `${options.name}: project view did not render`)
  assert(projectMetrics.hasCommandRail, `${options.name}: project command rail is missing`)
  assert(projectMetrics.hasProjectPlanList, `${options.name}: project progress plan list is missing`)
  assert(projectMetrics.hasNextStep, `${options.name}: project rail missing next step card`)
  assert(projectMetrics.hasRunPreview, `${options.name}: project main surface missing run preview`)
  assert(projectMetrics.hasWorkspaceStatus, `${options.name}: project main surface missing sync/status line`)
  assert(projectMetrics.hasPlanStatuses, `${options.name}: project plan rows missing status labels`)
  assert(projectMetrics.hasAgentHarnessEntry, `${options.name}: project main surface missing Agent Harness entry`)
  assert(projectMetrics.hasMemoryCapture, `${options.name}: project rail missing memory capture`)
  assert(projectMetrics.hasSeededMemory, `${options.name}: project-scoped memory is not visible`)
  assert(projectMetrics.hasSeededTodo, `${options.name}: seeded project todo is not visible`)
  if (options.mobile) assert(!projectMetrics.sidebarOpen, `${options.name}: mobile sidebar stayed open after project navigation`)
  if (options.mobile) assert(projectMetrics.hasProjectContextToggle, `${options.name}: mobile project context toggle is missing`)
  if (options.mobile) assert(projectMetrics.projectContextSheetOpen, `${options.name}: project context bottom sheet closed unexpectedly`)
  if (options.mobile) assert(projectMetrics.headerHasRoom, `${options.name}: mobile project header title overlaps actions`)
  if (options.mobile) assert(projectMetrics.headerClearsMobileTrigger, `${options.name}: mobile project header collides with navigation trigger`)
  assert(projectMetrics.composerHeight <= 118, `${options.name}: project composer is too tall at ${projectMetrics.composerHeight}px`)
  if (!options.mobile) {
    assert(projectMetrics.railWidth >= 340, `${options.name}: project rail is too narrow at ${projectMetrics.railWidth}px`)
  }
  assert(projectMetrics.scrollWidth <= projectMetrics.innerWidth, `${options.name}: project view horizontal overflow ${projectMetrics.scrollWidth} > ${projectMetrics.innerWidth}`)

  const projectScreenshot = await page.send("Page.captureScreenshot", { format: "png", fromSurface: true })
  await writeFile(path.join(RESULT_DIR, `${options.name}-project.png`), Buffer.from(projectScreenshot.data, "base64"))

  if (options.mobile) {
    await page.evaluate(`(() => {
      const close = document.querySelector('button[aria-label="Close project context"]');
      if (close instanceof HTMLButtonElement) close.click();
    })()`)
    await delay(200)
  }

  await page.evaluate(`(() => {
    const actions = document.querySelector('button[aria-label="Project actions"]');
    if (!(actions instanceof HTMLButtonElement)) throw new Error("Project actions button missing");
    actions.click();
  })()`)
  await delay(150)
  await page.evaluate(`(() => {
    const button = [...document.querySelectorAll("button")]
      .find((candidate) => (candidate.textContent || "").trim() === "Delete project");
    if (!(button instanceof HTMLButtonElement)) throw new Error("Delete project menu item missing");
    button.click();
  })()`)
  await delay(150)
  const deleteModalMetrics = await page.evaluate(`(() => {
    const text = document.body.innerText || "";
    return {
      hasDeleteModal: text.includes("Delete project?"),
      hasDeleteWarning: text.includes("Project memories remain in the memory system"),
      hasCloseButton: Boolean(document.querySelector('button[aria-label="Close delete project confirmation"]')),
    };
  })()`)
  assert(deleteModalMetrics.hasDeleteModal, `${options.name}: project delete confirmation modal did not open`)
  assert(deleteModalMetrics.hasDeleteWarning, `${options.name}: project delete confirmation lacks persistence warning`)
  assert(deleteModalMetrics.hasCloseButton, `${options.name}: project delete confirmation lacks close button`)
  const deleteModalScreenshot = await page.send("Page.captureScreenshot", { format: "png", fromSurface: true })
  await writeFile(path.join(RESULT_DIR, `${options.name}-project-delete-modal.png`), Buffer.from(deleteModalScreenshot.data, "base64"))
  await page.evaluate(`(() => {
    const close = document.querySelector('button[aria-label="Close delete project confirmation"]');
    if (!(close instanceof HTMLButtonElement)) throw new Error("Delete project modal close missing");
    close.click();
  })()`)
  await delay(150)

  await page.evaluate(`(() => {
    const composer = document.querySelector(".project-launch-composer");
    if (!(composer instanceof HTMLButtonElement)) throw new Error("Project launch composer missing");
    composer.click();
  })()`)
  await waitForPageCondition(
    page,
    `Boolean(document.querySelector(".chat-canvas .project-chip")) &&
      Boolean(document.querySelector(".progress-rail")) &&
      (document.body.innerText || "").includes("Wire agent-harness progress into project chats")`,
    5_000,
    `${options.name}: project chat did not finish rendering active project state`,
  )
  const projectChatMetrics = await page.evaluate(`(() => {
    const text = document.body.innerText || "";
    return {
      hasProjectChip: Boolean(document.querySelector(".project-chip")),
      hasProgressRail: Boolean(document.querySelector(".progress-rail")),
      hasPinnedPlan: text.includes("Project plan pinned") || text.includes("Agent running"),
      hasProjectTodo: text.includes("Wire agent-harness progress into project chats"),
      innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
    };
  })()`)
  assert(projectChatMetrics.hasProjectChip, `${options.name}: project chat did not show active project chip`)
  assert(projectChatMetrics.hasProgressRail, `${options.name}: project chat did not open progress rail`)
  assert(projectChatMetrics.hasPinnedPlan, `${options.name}: project chat progress rail missing pinned status`)
  assert(projectChatMetrics.hasProjectTodo, `${options.name}: project chat progress rail missing project todo`)
  assert(projectChatMetrics.scrollWidth <= projectChatMetrics.innerWidth, `${options.name}: project chat caused horizontal overflow`)
  const projectChatScreenshot = await page.send("Page.captureScreenshot", { format: "png", fromSurface: true })
  await writeFile(path.join(RESULT_DIR, `${options.name}-project-chat.png`), Buffer.from(projectChatScreenshot.data, "base64"))
}

async function assertContextCommand(appPort) {
  const commands = await fetchJson(`http://127.0.0.1:${appPort}/api/commands`)
  const hasContext = (commands.commands || []).some((command) => command.command === "/context")
  assert(hasContext, "slash command catalog is missing /context")
  const response = await fetch(`http://127.0.0.1:${appPort}/api/command`, {
    method: "POST",
    headers: JSON_MUTATION_HEADERS,
    body: JSON.stringify({ raw: "/context", session_id: SESSION_ID }),
  })
  if (!response.ok) {
    throw new Error(`/context command failed with ${response.status}: ${await response.text()}`)
  }
  const payload = await response.json()
  assert(String(payload.output || "").includes("used_tokens="), "/context did not return token usage")
}

async function seedSkillFixture(appPort) {
  const content = [
    "---",
    "name: visual-review",
    "description: Visual smoke review queue skill",
    "---",
    "",
    "# Visual Review",
    "",
    "Use this draft skill to verify the Skill Control Plane review queue.",
  ].join("\n")
  const response = await fetch(`http://127.0.0.1:${appPort}/api/skills`, {
    method: "POST",
    headers: JSON_MUTATION_HEADERS,
    body: JSON.stringify({ name: "visual-review", status: "review", content }),
  })
  if (!response.ok) {
    throw new Error(`Failed to seed review skill: ${response.status} ${await response.text()}`)
  }

  const statuses = ["active", "review", "disabled"]
  for (let index = 1; index <= 24; index += 1) {
    const name = `visual-bulk-skill-${String(index).padStart(2, "0")}`
    const bulkContent = [
      "---",
      `name: ${name}`,
      `description: Visual smoke bulk skill ${index}`,
      "---",
      "",
      `# ${name}`,
      "",
      "Use this skill to verify that the Skill Control Plane remains usable with a realistic skill catalog.",
    ].join("\n")
    const bulkResponse = await fetch(`http://127.0.0.1:${appPort}/api/skills`, {
      method: "POST",
      headers: JSON_MUTATION_HEADERS,
      body: JSON.stringify({
        name,
        status: statuses[index % statuses.length],
        content: bulkContent,
      }),
    })
    if (!bulkResponse.ok) {
      throw new Error(`Failed to seed bulk skill ${name}: ${bulkResponse.status} ${await bulkResponse.text()}`)
    }
  }
}

async function seedProjectFixture(appPort) {
  const createResponse = await fetch(`http://127.0.0.1:${appPort}/api/projects`, {
    method: "POST",
    headers: JSON_MUTATION_HEADERS,
    body: JSON.stringify({
      name: "Visual Smoke Project",
      description: "A seeded project for Geneva project surface and agent-harness progress checks.",
      context_md: "Keep visual QA scoped. Prefer small tasks, explicit progress, and project memory.",
      color: "#d97757",
      pinned: true,
    }),
  })
  if (!createResponse.ok) {
    throw new Error(`Failed to seed project: ${createResponse.status} ${await createResponse.text()}`)
  }
  const payload = await createResponse.json()
  const projectId = payload.project?.id
  if (!projectId) throw new Error("Seeded project did not return an id")

  const todoTexts = [
    "Audit the project surface against Claude Desktop",
    "Wire agent-harness progress into project chats",
    "Run visual smoke on desktop and mobile",
  ]
  for (const [index, text] of todoTexts.entries()) {
    const todoResponse = await fetch(`http://127.0.0.1:${appPort}/api/projects/${encodeURIComponent(projectId)}/todos`, {
      method: "POST",
      headers: JSON_MUTATION_HEADERS,
      body: JSON.stringify({ text }),
    })
    if (!todoResponse.ok) {
      throw new Error(`Failed to seed project todo: ${todoResponse.status} ${await todoResponse.text()}`)
    }
    const todoPayload = await todoResponse.json()
    if (index === 0) {
      const todoId = todoPayload.todo?.id
      await fetch(`http://127.0.0.1:${appPort}/api/projects/${encodeURIComponent(projectId)}/todos/${encodeURIComponent(todoId)}`, {
        method: "PUT",
        headers: JSON_MUTATION_HEADERS,
        body: JSON.stringify({ done: true }),
      })
    }
  }

  const sessionResponse = await fetch(`http://127.0.0.1:${appPort}/api/projects/${encodeURIComponent(projectId)}/sessions`, {
    method: "POST",
    headers: JSON_MUTATION_HEADERS,
    body: JSON.stringify({ session_id: SESSION_ID }),
  })
  if (!sessionResponse.ok) {
    throw new Error(`Failed to attach session to project: ${sessionResponse.status} ${await sessionResponse.text()}`)
  }

  const memoryResponse = await fetch(`http://127.0.0.1:${appPort}/api/memory`, {
    method: "POST",
    headers: JSON_MUTATION_HEADERS,
    body: JSON.stringify({
      content: "Visual smoke project memory should appear in the Project command rail.",
      scope: projectId,
      source_type: "visual_smoke",
      type: "project",
    }),
  })
  if (!memoryResponse.ok) {
    throw new Error(`Failed to seed project memory: ${memoryResponse.status} ${await memoryResponse.text()}`)
  }

  for (let index = 1; index <= 36; index += 1) {
    const extraProjectResponse = await fetch(`http://127.0.0.1:${appPort}/api/projects`, {
      method: "POST",
      headers: JSON_MUTATION_HEADERS,
      body: JSON.stringify({
        name: `Visual Smoke Extra ${String(index).padStart(2, "0")}`,
        description: "Extra project used to verify sidebar pagination and count stability.",
        color: index % 2 === 0 ? "#6f8f72" : "#8b7d6b",
      }),
    })
    if (!extraProjectResponse.ok) {
      throw new Error(`Failed to seed extra project: ${extraProjectResponse.status} ${await extraProjectResponse.text()}`)
    }
  }
}

function buildLedgerFixture() {
  const now = new Date().toISOString()
  return {
    id: "visual_smoke_context",
    session_id: SESSION_ID,
    event: "turn_context",
    created_at: now,
    model: "visual-smoke-model",
    trigger: "visual-smoke",
    budget: {
      context_window_tokens: 200000,
      effective_limit_tokens: 160000,
      percent_used: 37,
    },
    totals: {
      tokens_before: 24000,
      tokens_after: 8100,
      tokens_saved: 15900,
      entry_count: 4,
    },
    metadata: { audit_fixture: true },
    entries: [
      {
        source_type: "runtime_base_context",
        action: "included",
        label: "Runtime system prompt and tool schemas",
        tokens_before: 4200,
        tokens_after: 4200,
        tokens_saved: 0,
        reason: "Required base instructions for the agent harness.",
      },
      {
        source_type: "memory_context",
        action: "trimmed",
        label: "Long-term memories",
        tokens_before: 12800,
        tokens_after: 2600,
        tokens_saved: 10200,
        reason: "Memory retrieval exceeded the turn budget and was trimmed by relevance.",
      },
      {
        source_type: "tool_results",
        action: "compacted",
        label: "Tool result bloat guard",
        tokens_before: 6500,
        tokens_after: 900,
        tokens_saved: 5600,
        reason: "Oversized tool output was summarized before entering history.",
      },
      {
        source_type: "conversation_tail",
        action: "preserved",
        label: "Fresh conversation tail",
        tokens_before: 400,
        tokens_after: 400,
        tokens_saved: 0,
        reason: "Recent task state must stay verbatim.",
      },
    ],
  }
}

function buildSessionFixture() {
  const now = new Date().toISOString()
  return {
    session_id: SESSION_ID,
    provider: "visual-smoke",
    model: "visual-smoke-model",
    created_at: now,
    updated_at: now,
    conversation: {
      max_history: 100,
      messages: [
        {
          role: "user",
          content: "Read the project context.",
          timestamp: now,
          _is_internal: false,
        },
        {
          role: "assistant",
          content: [
            { type: "text", text: "I will inspect the relevant context first." },
            {
              type: "tool_use",
              id: "toolu_visual_read",
              name: "Read",
              input: { file_path: "context/goals.md" },
            },
          ],
          timestamp: now,
          _is_internal: false,
        },
        {
          role: "user",
          content: [
            {
              type: "tool_result",
              tool_use_id: "toolu_visual_read",
              content: "Goals loaded.",
              is_error: false,
            },
          ],
          timestamp: now,
          _is_internal: false,
        },
        {
          role: "assistant",
          content: "Context loaded and ready.",
          timestamp: now,
          _is_internal: false,
        },
        ...buildLongChatFixture(now),
      ],
    },
  }
}

function buildLongChatFixture(now) {
  return Array.from({ length: 7 }, (_, index) => [
    {
      role: "user",
      content: `Stress message ${index + 1}: explain how the memory layer should stay stable while the user scrolls.`,
      timestamp: now,
      _is_internal: false,
    },
    {
      role: "assistant",
      content: [
        "The chat surface should keep the user's reading position stable while new tokens stream.",
        "",
        "- Only pin to bottom when the user is already near the bottom.",
        "- Contain overscroll inside the message viewport.",
        "- Keep actions small enough that typography stays calm.",
        "",
        "This fixture exists to make the viewport scrollable during visual smoke.",
      ].join("\n"),
      timestamp: now,
      _is_internal: false,
    },
  ]).flat()
}

class CdpPage {
  constructor(webSocketDebuggerUrl) {
    this.ws = new WebSocket(webSocketDebuggerUrl)
    this.nextId = 0
    this.pending = new Map()
    this.listeners = new Set()
    this.ready = new Promise((resolve, reject) => {
      this.ws.onopen = resolve
      this.ws.onerror = reject
    })
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      if (message.id && this.pending.has(message.id)) {
        const { resolve, reject } = this.pending.get(message.id)
        this.pending.delete(message.id)
        if (message.error) reject(new Error(message.error.message || JSON.stringify(message.error)))
        else resolve(message.result || {})
        return
      }
      for (const listener of this.listeners) listener(message)
    }
  }

  on(type, listener) {
    if (type === "event") this.listeners.add(listener)
  }

  async send(method, params = {}) {
    await this.ready
    const id = ++this.nextId
    this.ws.send(JSON.stringify({ id, method, params }))
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject })
      setTimeout(() => {
        if (this.pending.delete(id)) reject(new Error(`CDP timeout: ${method}`))
      }, 10_000)
    })
  }

  async evaluate(expression) {
    const result = await this.send("Runtime.evaluate", { expression, returnByValue: true })
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.text || "Runtime evaluation failed")
    return result.result?.value
  }
}

async function openCdpPage(cdpPort) {
  const targets = await fetchJson(`http://127.0.0.1:${cdpPort}/json/list`)
  const target = targets.find((item) => item.type === "page") || targets[0]
  return new CdpPage(target.webSocketDebuggerUrl)
}

async function waitForReady(page) {
  const start = Date.now()
  while (Date.now() - start < 10_000) {
    const ready = await page.evaluate("document.readyState")
    const hasRoot = await page.evaluate("Boolean(document.querySelector('.chat-canvas'))")
    if ((ready === "interactive" || ready === "complete") && hasRoot) return
    await delay(100)
  }
  throw new Error("Timed out waiting for app to render")
}

async function waitForPageCondition(page, expression, timeoutMs, message) {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    const matched = await page.evaluate(`Boolean(${expression})`)
    if (matched) return
    await delay(100)
  }
  throw new Error(message)
}

async function findChrome() {
  for (const candidate of CHROME_CANDIDATES) {
    try {
      const probe = spawn(candidate, ["--version"], { stdio: "ignore" })
      const ok = await new Promise((resolve) => {
        probe.on("exit", (code) => resolve(code === 0))
        probe.on("error", () => resolve(false))
      })
      if (ok) return candidate
    } catch {
      // Try the next candidate.
    }
  }
  throw new Error("Chrome/Chromium binary not found. Set CHROME_BIN to run visual smoke.")
}

function captureProcessLog(child, label) {
  const lines = []
  const capture = (chunk) => {
    const text = chunk.toString()
    lines.push(...text.split(/\r?\n/).filter(Boolean).map((line) => `[${label}] ${line}`))
    while (lines.length > 40) lines.shift()
  }
  child.stdout.on("data", capture)
  child.stderr.on("data", capture)
  return lines
}

async function freePort() {
  return new Promise((resolve, reject) => {
    const server = createServer()
    server.listen(0, "127.0.0.1", () => {
      const address = server.address()
      server.close(() => resolve(address.port))
    })
    server.on("error", reject)
  })
}

async function waitForHttp(url, timeoutMs, logLines) {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    try {
      const response = await fetch(url)
      if (response.ok) return
    } catch {
      // Keep waiting.
    }
    await delay(150)
  }
  throw new Error(`Timed out waiting for ${url}\n${logLines.join("\n")}`)
}

async function fetchJson(url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`GET ${url} failed with ${response.status}`)
  return response.json()
}

function assert(condition, message) {
  if (!condition) throw new Error(message)
}

function blockingPageErrors(errors) {
  return errors.filter((error) => !/429 \(Too Many Requests\)|status of 429/i.test(error))
}

function safeSessionId(sessionId) {
  const digest = createHash("sha256").update(sessionId, "utf8").digest("hex").slice(0, 16)
  const visible = sessionId
    .split("")
    .map((char) => (/[a-zA-Z0-9_-]/.test(char) ? char : "_"))
    .join("")
    .slice(0, 80)
  return `${visible || "unknown"}-${digest}`
}

function themeOptionLabel(mode) {
  if (mode === "dark") return "Dark"
  if (mode === "light") return "Light"
  return "System"
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function terminateProcess(child) {
  if (!child || child.exitCode !== null || child.signalCode !== null) return
  const exited = new Promise((resolve) => child.once("exit", () => resolve(true)))
  child.kill("SIGTERM")
  const closed = await Promise.race([exited, delay(1500).then(() => false)])
  if (closed) return
  child.kill("SIGKILL")
  await Promise.race([exited, delay(1000)])
}

async function safeRm(target, options) {
  if (!target) return
  for (let attempt = 0; attempt < 5; attempt += 1) {
    try {
      await rm(target, options)
      return
    } catch (error) {
      if (attempt === 4) {
        console.warn(`visual smoke cleanup skipped ${target}: ${error.message}`)
        return
      }
      await delay(120 * (attempt + 1))
    }
  }
}

await main()
