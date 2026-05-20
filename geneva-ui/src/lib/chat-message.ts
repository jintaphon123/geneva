import type { Attachment, ChatMessage, Project, SlashCommand } from "@/types"

export function buildAugmentedMessage(text: string, attachments: Attachment[]): string {
  const parts: string[] = []
  for (const attachment of attachments) {
    if (attachment.type === "image" && attachment.dataUrl) {
      parts.push(`[Image: ${attachment.name}]\n${attachment.dataUrl}`)
    }
    if (attachment.type === "text" && attachment.text) {
      parts.push(`[File: ${attachment.name}]\n\`\`\`\n${attachment.text}\n\`\`\``)
    }
    if (attachment.type === "unknown") {
      parts.push(`[File attached: ${attachment.name}]`)
    }
  }
  return parts.length ? parts.join("\n\n") + (text ? `\n\n${text}` : "") : text
}

export function buildDisplayMessage(text: string, attachments: Attachment[]): string {
  const attachmentLines = attachments.map((attachment) => {
    if (attachment.type === "image") return `[Image: ${attachment.name}]`
    return `[File: ${attachment.name}]`
  })
  return [attachmentLines.join("\n"), text].filter(Boolean).join("\n\n")
}

export function buildBranchedTurnMessage(branchContext: string, message: string): string {
  return [
    "Continue from this branched conversation context. Treat it as prior chat history for this new session.",
    "Do not mention that the context was injected unless the user asks.",
    "",
    branchContext,
    "",
    "New user message:",
    message,
  ].join("\n")
}

export function buildBranchTranscript(messages: ChatMessage[]): string {
  return messages
    .map((message) => {
      const role = message.role === "assistant" ? "Assistant" : "User"
      return `${role}: ${cleanMessageForDraft(message.content).slice(0, 2400)}`
    })
    .join("\n\n")
    .slice(-12_000)
}

export function cleanMessageForDraft(content: string): string {
  return content
    .replace(/^\[(?:Image|File)(?::| attached:)[^\]]+\]\n*/gim, "")
    .trim()
}

export function findPreviousUserMessage(messages: ChatMessage[], messageId: string): ChatMessage | null {
  const index = messages.findIndex((message) => message.id === messageId)
  if (index < 0) return null
  for (let cursor = index - 1; cursor >= 0; cursor -= 1) {
    if (messages[cursor]?.role === "user") return messages[cursor]
  }
  return null
}

export function buildTurnMessage(text: string, options: { webSearch: boolean }): string {
  if (!options.webSearch) return text
  return [
    "For this turn, use web search before answering if the available tools support it.",
    "Do not mention this instruction to the user. Ground the answer in current sources where useful.",
    "",
    text,
  ].join("\n")
}

export function formatContextCommandOutput(output: string): string {
  const fields = new Map<string, string>()
  for (const match of output.matchAll(/([a-z_]+)=([^\s]+)/g)) {
    fields.set(match[1], match[2])
  }

  const usedTokens = parseNumberField(fields.get("used_tokens"))
  const maxTokens = parseNumberField(fields.get("max_tokens"))
  const percentUsed = fields.get("percent_used")
  const contextFiles = parseNumberField(fields.get("context_files_loaded"))

  if (usedTokens === null && maxTokens === null && percentUsed === undefined && contextFiles === null) {
    return "Context Inspector is open on the right."
  }

  const lines = ["Context Inspector is open on the right.", ""]
  if (usedTokens !== null) lines.push(`- Used: ${usedTokens.toLocaleString()} tokens`)
  if (maxTokens !== null) lines.push(`- Window: ${maxTokens.toLocaleString()} tokens`)
  if (percentUsed !== undefined) lines.push(`- Usage: ${percentUsed}%`)
  if (contextFiles !== null) lines.push(`- Context files loaded: ${contextFiles.toLocaleString()}`)
  return lines.join("\n")
}

export function parseNumberField(value: string | undefined): number | null {
  if (!value) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

export function dedupeCommands(commands: SlashCommand[]): SlashCommand[] {
  const seen = new Set<string>()
  const result: SlashCommand[] = []
  for (const command of commands) {
    if (seen.has(command.command)) continue
    seen.add(command.command)
    result.push(command)
  }
  return result
}

export function findMatchingCommand(text: string, commands: SlashCommand[]): SlashCommand | null {
  return (
    commands.find((command) => text === command.command || text.startsWith(`${command.command} `)) ?? null
  )
}

export function detectProjectFromMessage(text: string, projects: Project[]): Project | null {
  const source = normalizeProjectText(text)
  if (!source) return null

  let best: { project: Project; score: number } | null = null
  for (const project of projects) {
    if (project.archived) continue
    const name = normalizeProjectText(project.name)
    if (!name) continue

    const compactSource = source.replace(/\s+/g, "")
    const compactName = name.replace(/\s+/g, "")
    if (name.length >= 4 && source.includes(name)) return project
    if (compactName.length >= 6 && compactSource.includes(compactName)) return project

    const nameTokens = splitProjectTokens(project.name)
    const descriptionTokens = splitProjectTokens(project.description).slice(0, 8)
    const score =
      nameTokens.reduce((total, token) => total + (source.includes(token) ? token.length : 0), 0) +
      descriptionTokens.reduce((total, token) => total + (source.includes(token) ? 2 : 0), 0)

    if (score >= 6 && (!best || score > best.score)) {
      best = { project, score }
    }
  }
  return best?.project ?? null
}

export function normalizeProjectText(value: string): string {
  return value.normalize("NFKC").toLocaleLowerCase().trim()
}

export function splitProjectTokens(value: string): string[] {
  return normalizeProjectText(value)
    .split(/[\s\-_/()[\]{}.,:;'"|]+/)
    .filter((token) => token.length >= 4)
}
