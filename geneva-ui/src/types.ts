export type SessionSummary = {
  session_id: string
  title?: string
  pinned?: boolean
  project_id?: string
  project_name?: string
  project_color?: string
  created_at?: string
  updated_at?: string
  provider?: string
  model?: string
  message_count?: number | string
  date_bucket?: "today" | "yesterday" | "this_week" | "older" | string
}

export type MemoryItem = {
  id: string
  path: string
  name: string
  type: string
  status: string
  content: string
  confidence: number
  importance: number
  source_type: string
  created_at: string
  updated_at: string | null
  retention_days: number
  expires_at: string | null
  superseded_by: string | null
  scope: string | null
  fts_score: number
  source_session_id?: string | null
  captured_at?: string | null
  events?: MemoryEvent[]
}

export type MemoryEvent = {
  id: string
  event_type: string
  payload: unknown
  created_at: string
}

export type MemoryWriteEvent = {
  id: string
  memory_id: string
  session_id?: string | null
  turn_id?: string | null
  project_id?: string | null
  write_type: "auto_saved" | "draft" | "explicit" | "imported" | string
  confidence?: number | null
  sensitivity?: "public" | "private" | "restricted" | string | null
  user_visible_text: string
  source_excerpt?: string | null
  status: "saved" | "draft" | "undone" | "dismissed" | "edited" | string
  created_at: string
  updated_at?: string | null
}

export type MemoryWriteEventListResult = {
  items: MemoryWriteEvent[]
  total: number
  has_more: boolean
}

export type MemoryListResult = {
  items: MemoryItem[]
  total: number
  has_more: boolean
}

export type MemoryConflict = {
  id: string
  existing_memory_id: string
  existing_name?: string | null
  existing_content?: string | null
  existing_type?: string | null
  existing_memory_kind?: string | null
  existing_scope?: string | null
  proposed_content: string
  proposed_type: string
  proposed_scope?: string | null
  proposed_memory_kind?: string | null
  proposed_source_type?: string | null
  proposed_confidence?: number | null
  proposed_importance?: number | null
  conflict_type: string
  reason: string
  similarity: number
  token_overlap: number
  status: string
  resolution?: string | null
  resolved_memory_id?: string | null
  created_at: string
  updated_at?: string | null
  resolved_at?: string | null
}

export type MemoryConflictListResult = {
  items: MemoryConflict[]
  total: number
  has_more: boolean
}

export type MemoryTimeline = { day: string; count: number; ids: string[] }[]

export type MemoryStats = {
  active: number
  superseded: number
  archived: number
  expired: number
  lastIndexed: string | null
  recent: MemoryItem[]
}

export type ContextLedgerEntry = {
  source_type: string
  action: "included" | "trimmed" | "compacted" | "preserved" | "omitted" | string
  tokens_before: number
  tokens_after: number
  tokens_saved?: number
  reason: string
  label?: string
  source_id?: string | null
  message_count?: number
  chars?: number
  metadata?: Record<string, unknown>
}

export type ContextLedgerRecord = {
  id: string
  session_id: string
  event: "turn_context" | "compact" | string
  created_at: string
  model: string
  trigger: string
  budget?: Record<string, unknown>
  totals?: {
    tokens_before?: number
    tokens_after?: number
    tokens_saved?: number
    entry_count?: number
  }
  metadata?: Record<string, unknown>
  entries: ContextLedgerEntry[]
}

export type ContextLedgerPayload = {
  session_id: string
  latest?: ContextLedgerRecord | null
  history?: ContextLedgerRecord[]
  records?: ContextLedgerRecord[]
}

export type ContextDisclosureSummary = {
  session_id?: string | null
  turn_id?: string | null
  ledger_id?: string | null
  summary: string
  counts: {
    projects?: number
    memories?: number
    sources?: number
    skills?: number
    tools?: number
  }
  projects?: string[]
  skills?: string[]
  tools?: string[]
  mode?: { id?: string | null; label?: string | null } | null
  mode_id?: string | null
  mode_label?: string | null
  route_reason?: string | null
  cost_tier?: string | null
  model?: string | null
  ghost_mode?: boolean
  no_memory_write?: boolean
  trimmed?: boolean
  budget?: Record<string, unknown>
  created_at?: string | null
}

export type ArtifactRecord = {
  artifact_id: string
  type: "screenshot" | "citation_map" | "document_preview" | "research_trace" | "research_report" | "tool_output" | string
  session_id: string | null
  created_at: string
  expires_at: string | null
  size_bytes: number
  redacted: boolean | number
}

export type ArtifactDetail = ArtifactRecord & {
  content?: string | null
  content_path?: string | null
}

export type ResearchSource = {
  id?: string
  run_id?: string
  source_id: string
  project_source_id?: string | null
  title: string
  url?: string
  publisher?: string
  credibility_score?: number | null
  credibility_tier?: number | null
  used_in_report?: boolean
  metadata?: Record<string, unknown>
  created_at?: string
}

export type ResearchRun = {
  id: string
  session_id: string | null
  project_id: string | null
  mode: string
  query: string
  plan: Record<string, unknown>
  status: "draft_plan" | "running" | "stopped" | "completed" | "failed" | string
  artifact_id: string | null
  final_text: string
  error: string | null
  metadata: Record<string, unknown>
  created_at: string
  updated_at: string
  started_at: string | null
  completed_at: string | null
  sources: ResearchSource[]
}

export type ResearchRunListResult = {
  runs: ResearchRun[]
  count: number
}

export type ResearchProgressItem = {
  step: number
  total: number
  label: string
  detail: string
  status: "running" | "complete" | "error" | "stopped" | string
}

export type ChatMessage = {
  id: string
  role: "user" | "assistant"
  content: string
  researchQuery?: string
  researchPlan?: { title: string; steps: string[]; query: string }
  researchRunId?: string | null
  researchArtifactId?: string | null
  researchSources?: ResearchSource[]
  researchQualityScore?: Record<string, unknown>
  researchProgress?: ResearchProgressItem[]
  researchStatus?: "planning" | "running" | "completed" | "stopped" | "failed" | string
  remembered?: boolean
  loading?: boolean
  error?: string | null
  skillName?: string
  skillDescription?: string
  skillSafetyStatus?: string | null
  skillInvocationScope?: SkillInvocationScope
  toolEvents?: ToolTraceEvent[]
  activityEvents?: ActivityEvent[]
  contextSummary?: ContextDisclosureSummary | null
  timestamp?: string
  serverId?: string
}

export type SkillInvocationScope = "once" | "chat" | "project" | "global"

export type ActivityEvent = {
  id: string
  kind:
    | "memory"
    | "thinking"
    | "tool"
    | "permission"
    | "memory_update"
    | "error"
    | "complete"
    | "heartbeat"
  title: string
  detail?: string
  status: "queued" | "running" | "waiting" | "complete" | "error" | "timeout" | "limit" | "info" | string
  timestamp?: number
  durationMs?: number | null
  timeoutSeconds?: number | null
  toolName?: string | null
  error?: string | null
}

export type ToolTraceEvent = {
  id: string
  toolCallId?: string | null
  toolName: string
  status: "queued" | "running" | "complete" | "error" | "timeout" | "limit" | string
  summary?: string
  inputPreview?: string
  outputPreview?: string
  error?: string | null
  durationMs?: number | null
  timeoutSeconds?: number | null
  turnIndex?: number | null
}

export type ToolPermissionRequest = {
  requestId: string
  sessionId: string
  toolName: string
  message: string
  suggestion?: string | null
  timeoutSeconds: number
}

export type SessionActivityItem = {
  turn_id?: string | null
  created_at?: string | null
  user_preview?: string
  tool_names?: string[]
  memory_action?: string | null
  error_count?: number
}

export type SessionActivityPayload = {
  session_id: string
  activities: SessionActivityItem[]
}

export type AgentTraceRecord = {
  session_id: string
  created_at: string
  user_message_preview: string
  assistant_preview: string
  memory_action?: string | null
  memory_active_chars?: number | null
  events: Array<{
    tool_name: string
    kind: string
    status: string
    summary: string | null
    input_preview: string | null
    output_preview: string | null
    duration_ms: number | null
    tool_call_id: string | null
    is_error: boolean
    error: string | null
    timeout_seconds: number | null
    turn_index: number | null
  }>
}

export type SlashCommand = {
  name: string
  level: "client" | "server" | "skill"
  description: string
  command: string
  params: string[]
}

export type SearchResultType = "chat" | "project" | "memory" | "source" | "research_report" | string

export type SearchResultAction = {
  id?: string
  type?: string
  label?: string
  target?: string
  session_id?: string | null
  project_id?: string | null
  source_id?: string | null
  memory_id?: string | null
  artifact_id?: string | null
  run_id?: string | null
}

export type SearchResult = {
  id: string
  type: SearchResultType
  title: string
  snippet: string
  matched_fields: string[]
  score: number
  scope: string
  project_id: string | null
  session_id: string | null
  source_id: string | null
  artifact_id: string | null
  badges: string[]
  actions: SearchResultAction[]
  created_at: string
  metadata: Record<string, unknown>
}

export type SearchGroup = {
  type: SearchResultType
  count: number
  results: SearchResult[]
}

export type SearchPayload = {
  query: string
  results: SearchResult[]
  groups: Record<string, SearchGroup>
  count: number
  limit: number
}

export type ToolSpecMeta = {
  name: string
  description: string
  input_schema: Record<string, unknown>
  aliases: string[]
  is_read_only: boolean
  is_destructive: boolean
  strict: boolean
  max_result_size_chars: number
  timeout_seconds: number
  profile?: string
}

export type SkillMeta = {
  name: string
  description: string
  command: string
  triggers: string[]
  enabled: boolean
  status: "review" | "active" | "disabled" | "archived" | string
  source?: string
  safety_status?: "passed" | "warning" | "blocked" | string
  safety_findings?: string[]
  usage_count?: number
  last_used_at?: string | null
  checksum?: string
  generated_from?: string | null
  source_session_id?: string | null
  review_notes?: string[]
  path?: string
  eval_cases?: SkillEvalCase[]
  revisions?: SkillRevision[]
  feedback?: SkillFeedback[]
  feedback_summary?: SkillFeedbackSummary
}

export type SkillEvalCase = {
  id: string
  input: string
  expected: string
  status: "pending" | "passed" | "failed" | string
  actual?: string
  notes?: string
  created_at: string
  updated_at: string
}

export type SkillRevision = {
  id: string
  checksum: string
  source: string
  note?: string
  created_at: string
  content_preview?: string
}

export type SkillFeedback = {
  id: string
  score: number
  outcome: string
  note?: string
  suggested_change?: string
  source_session_id?: string | null
  created_at: string
}

export type SkillFeedbackSummary = {
  count: number
  average_score: number | null
  positive: number
  negative: number
}

export type Attachment = {
  id: string
  name: string
  type: "image" | "text" | "unknown"
  dataUrl?: string
  text?: string
  size: number
}

export type CodeRunResult = {
  ok: boolean
  kind: "html" | "text"
  output: string
  error: string
  language: string
}

export type Todo = {
  id: string
  project_id: string
  text: string
  done: boolean
  position: number
  created_at: string
  updated_at: string
}

export type Project = {
  id: string
  name: string
  description: string
  context_md: string
  color: string
  pinned: boolean
  archived: boolean
  created_at: string
  updated_at: string
  todos: Todo[]
  session_count: number
}

export type ProjectSourceStatus = "pending" | "ready" | "failed" | "unsupported" | "stale" | string

export type ProjectSourceIncludePolicy = "include" | "exclude" | string

export type ProjectSource = {
  id: string
  project_id: string
  source_type: "text" | "markdown" | "url" | "pdf" | "docx" | string
  title: string
  uri: string
  content_hash: string
  snapshot_path: string
  parse_status: ProjectSourceStatus
  include_policy: ProjectSourceIncludePolicy
  token_estimate: number
  metadata: Record<string, unknown>
  parse_error: string | null
  created_at: string
  updated_at: string
  last_indexed_at: string | null
}

export type ProjectSourcePreview = {
  preview: string
  sources: ProjectSource[]
  count: number
}

export type SettingsConfig = {
  anthropic_api_key: string
  openrouter_api_key: string
  google_api_key: string
  gemini_cli_path: string
  codex_cli_path: string
  default_provider: string
  default_model: string
  research_model: string
  fast_model: string
  default_mode: string
  geneva_dir: string
  mybrain_dir: string
  dark_mode: boolean
}

export type MemoryBrowserStats = {
  by_status?: Record<string, number>
  by_type?: Record<string, number>
  conflicts_by_status?: Record<string, number>
}

export type SystemStatus = {
  version: string
  memory_count: number
  skills_count: number
  gemini_ok: boolean
  codex_ok: boolean
  geneva_dir: string
}

export type ModeProfile = {
  id: string
  label: string
  description: string
  provider: string
  provider_name?: string
  model: string
  primary_model: string
  fallback_model: string
  context_budget_tokens: number
  tool_autonomy: string
  research_depth: string
  cost_tier: string
  latency_tier: string
  background_policy: string
  default?: boolean
  is_default?: boolean
}

export type ModeListResult = {
  default_mode_id: string
  modes: ModeProfile[]
}

export type ConnectorStatus = {
  connector: string
  configured: boolean
  capabilities: string[]
  oauth_required_for?: string[]
}

export type ConnectorsResult = {
  connectors: ConnectorStatus[]
  trusted_servers: string[]
}

export type UsageSummary = {
  sessions_count: number
  entry_count: number
  total_tokens: number
  total_cost_usd: number
  by_model: Array<{
    model: string
    tokens: number
    cost_usd: number
  }>
  recent_sessions: Array<{
    session_id: string
    saved_at: string
    tokens: number
    cost_usd: number
  }>
}

export type OnboardingStatus = {
  needs_onboarding?: boolean
  complete?: boolean
}

export type StreamPayload = {
  turn_id?: string
  event_seq?: number
  type?: string
  data?: Record<string, unknown>
  timestamp?: number
  tool_call_id?: string | null
  error?: {
    code?: string
    message?: string
    recoverable?: boolean
    suggestion?: string
  } | null
}
