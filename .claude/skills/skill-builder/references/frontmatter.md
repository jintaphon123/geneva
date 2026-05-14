# Frontmatter & Technical Reference

Complete technical reference for Claude Code skills — all frontmatter fields, advanced patterns, argument passing, troubleshooting, and how skills fit into your project.

Source: https://code.claude.com/docs/en/skills

---

## Understanding CLAUDE.md vs Skills

| | CLAUDE.md | Skill |
|---|---|---|
| **When loaded** | Every conversation, always | Only when invoked (via `/name` or auto-detection) |
| **What it's for** | Project-wide rules, conventions, context | Specific task workflows, specialized procedures |
| **Size concern** | Always in context, so keep it focused | Only loaded when needed, but keep under 500 lines |
| **Examples** | "Use TypeScript for all files", "Run tests before committing" | "Generate a PR summary", "Create meeting notes", "Deploy to staging" |

**Rule of thumb:** If Claude should *always* know it, put it in CLAUDE.md. If Claude should only know it when doing a specific task, make it a skill.

CLAUDE.md instructions still apply inside a skill's execution. A skill inherits your project's rules — it doesn't override them.

---

## Frontmatter Field Reference

All fields are optional. Only `description` is recommended.

| Field | Required | Type | Default | Description |
|-------|----------|------|---------|-------------|
| `name` | No | string | directory name | Display name and `/slash-command`. Lowercase letters, numbers, hyphens only. Max 64 chars. |
| `description` | Recommended | string | first paragraph of content | What the skill does and when to use it. Claude uses this for auto-invocation decisions. |
| `argument-hint` | No | string | none | Autocomplete hint for expected arguments. Shown in `/` menu. Examples: `[issue-number]`, `[filename] [format]` |
| `disable-model-invocation` | No | boolean | `false` | When `true`, only the user can invoke the skill. Removes it from Claude's context entirely. |
| `user-invocable` | No | boolean | `true` | When `false`, hides the skill from the `/` menu. Only Claude can invoke it. |
| `allowed-tools` | No | string (comma-separated) | all tools | Tools available without permission prompts when this skill is active. |
| `model` | No | string | inherit | Model to use: `sonnet`, `opus`, `haiku`, or omit to inherit. |
| `context` | No | string | none | Set to `fork` to run in an isolated subagent context. |
| `agent` | No | string | `general-purpose` | Subagent type when `context: fork` is set. Options: `Explore`, `Plan`, `general-purpose`, or any custom agent name. |
| `hooks` | No | object | none | Lifecycle hooks scoped to this skill. See Hooks section below. |

---

## Invocation Control Matrix

| Frontmatter | User can invoke? | Claude can invoke? | When loaded into context |
|-------------|------------------|--------------------|--------------------------|
| (default — both omitted) | Yes | Yes | Description always in context. Full skill loads when invoked. |
| `disable-model-invocation: true` | Yes | No | Description NOT in context. Full skill loads when user invokes. |
| `user-invocable: false` | No | Yes | Description always in context. Full skill loads when Claude invokes. |

Key nuances:
- `user-invocable` only controls `/` menu visibility, NOT the Skill tool. To block programmatic invocation, use `disable-model-invocation: true`.
- `disable-model-invocation: true` is the strongest restriction. It removes the skill from Claude's context entirely AND prevents Skill tool access.

---

## String Substitutions

| Variable | Description | Example |
|----------|-------------|---------|
| `$ARGUMENTS` | All arguments passed when invoking the skill | `/fix-issue 123` → `$ARGUMENTS` = `123` |
| `$ARGUMENTS[N]` | Specific argument by 0-based index | `$ARGUMENTS[0]` = first arg |
| `$N` | Shorthand for `$ARGUMENTS[N]` | `$0` = first arg, `$1` = second |
| `${CLAUDE_SESSION_ID}` | Current session ID | Useful for logs, session-specific files |

**Automatic fallback:** If `$ARGUMENTS` is NOT present anywhere in the skill content, arguments are automatically appended as `ARGUMENTS: <value>` at the end.

**Example with positional arguments:**

```yaml
---
name: migrate-component
description: Migrate a component from one framework to another
argument-hint: [component] [from-framework] [to-framework]
---

Migrate the $0 component from $1 to $2.
Preserve all existing behavior and tests.
```

Running `/migrate-component SearchBar React Vue` replaces `$0` with `SearchBar`, `$1` with `React`, `$2` with `Vue`.

---

## Skill File Locations

| Location | Path | Applies to | Priority |
|----------|------|------------|----------|
| Enterprise | Managed settings | All users in org | Highest |
| Personal | `~/.claude/skills/<name>/SKILL.md` | All your projects | High |
| Project | `.claude/skills/<name>/SKILL.md` | This project only | Medium |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | Where plugin enabled | Lowest |

When skills share the same name across levels, higher-priority locations win. Plugin skills use `plugin-name:skill-name` namespace so they cannot conflict.

**Monorepo support:** When editing files in subdirectories, Claude Code auto-discovers skills from nested `.claude/skills/` directories.

**Additional directories:** Skills in `.claude/skills/` within `--add-dir` directories are loaded automatically with live change detection.

---

## `allowed-tools` Syntax Guide

The `allowed-tools` field restricts which tools Claude can use without permission prompts when a skill is active. Your global permission settings still apply on top of this.

**Basic syntax:**

```yaml
allowed-tools: Read, Grep, Glob
```

**Tool-specific patterns with globs:**

```yaml
allowed-tools: Bash(git *), Bash(npm test), Read
```

| Pattern | What it allows |
|---------|---------------|
| `Bash` | Any bash command (no restriction) |
| `Bash(git *)` | Any command starting with `git` |
| `Bash(npm test)` | Only the exact command `npm test` |
| `Bash(python scripts/*)` | Python on any file in `scripts/` |
| `Read` | Read any file (no restriction on arguments) |

**Common patterns:**

```yaml
# Read-only skill (no file modifications)
allowed-tools: Read, Grep, Glob

# Can only run specific commands
allowed-tools: Bash(git status), Bash(git diff), Read

# Can only use web tools
allowed-tools: WebSearch, WebFetch

# Can read files and run a specific script
allowed-tools: Read, Glob, Bash(python scripts/analyze.py *)
```

**Important:** `allowed-tools` adds *additional* auto-approvals on top of your existing permission settings. It doesn't remove permissions you've already granted globally.

---

## Advanced Patterns

### Dynamic Context Injection

The `` !`command` `` syntax runs shell commands BEFORE the skill content is sent to Claude. The command output replaces the placeholder inline.

```yaml
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: Explore
allowed-tools: Bash(gh *)
---

## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
- Changed files: !`gh pr diff --name-only`

## Your task
Summarize this pull request...
```

This is preprocessing. Claude only sees the final result, not the commands.

**Use cases:**
- Injecting git status, branch info, or diff data
- Fetching live API responses
- Reading environment variables or config files
- Getting file listings or project metadata

### Running Skills in a Subagent (context: fork)

Add `context: fork` to run a skill in an isolated subagent context. The skill content becomes the subagent's task prompt. The subagent does NOT have access to your conversation history.

**When to use `context: fork`:**
- The task is self-contained and doesn't need conversation history
- The skill produces verbose output you want to keep out of main context
- You want to enforce tool restrictions via the agent type
- The skill is computationally expensive and a cheaper model suffices

**When NOT to use `context: fork`:**
- The skill contains guidelines without a concrete task (subagent returns nothing useful)
- The skill needs back-and-forth conversation with the user
- The skill needs context from the current conversation

**Agent options:**
- `Explore` — Haiku, read-only. Best for research, file discovery, code search.
- `Plan` — Inherits model, read-only. Best for planning research.
- `general-purpose` — Inherits model, all tools. Best for complex multi-step tasks.
- Any custom agent name from `.claude/agents/`.

### Supporting Files

```
my-skill/
  SKILL.md              # Main instructions (required, <500 lines)
  references/           # Detailed docs loaded only when needed
  scripts/
    helper.py           # Utility script
```

Reference them from SKILL.md so Claude knows they exist. Supporting files are NOT loaded automatically.

### Hooks in Skills

Skills can define lifecycle hooks in frontmatter. These hooks only run while the skill is active.

```yaml
---
name: safe-editor
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/run-linter.sh"
---
```

| Event | Matcher input | When it fires |
|-------|---------------|---------------|
| `PreToolUse` | Tool name | Before the skill uses a tool |
| `PostToolUse` | Tool name | After the skill uses a tool |
| `Stop` | (none) | When the skill finishes |

Hook commands receive JSON input via stdin. Exit code 0 = allow, exit code 2 = block.

### Visual Output (Bundled Scripts)

Skills can bundle scripts that generate visual output (HTML, images, charts):

```yaml
---
name: codebase-visualizer
description: Generate an interactive tree visualization of your codebase
allowed-tools: Bash(python *)
---

Run the visualization script:
```bash
python ~/.claude/skills/codebase-visualizer/scripts/visualize.py .
```
```

### Extended Thinking (Ultrathink)

Include the word `ultrathink` anywhere in your skill content to activate extended thinking mode.

**When to use it:**
- Complex analysis requiring weighing multiple factors
- Architecture decisions with trade-offs
- Debugging tasks where root cause analysis matters

```yaml
---
name: architecture-review
---

ultrathink

Review the following codebase architecture...
```

---

## Permissions and Access Control

Three ways to control which skills Claude can invoke:

**1. Disable all skills** by denying the Skill tool in `/permissions`:
```
Skill
```

**2. Allow or deny specific skills:**
```
Skill(commit)          # Allow exact match
Skill(review-pr *)     # Allow with any arguments
Skill(deploy *)        # Deny pattern
```

**3. Hide individual skills** with `disable-model-invocation: true` in frontmatter.

---

## Troubleshooting

### Skill not triggering

1. **Check the description** — Does it include keywords users would naturally say?
2. **Verify it's visible** — Ask "What skills are available?"
3. **Rephrase your request** — Try wording that more closely matches the description.
4. **Invoke directly** — Use `/skill-name` to confirm the skill works at all.
5. **Check `disable-model-invocation`** — If `true`, Claude cannot auto-invoke.

### Skill triggers too often

1. **Make the description more specific** — Narrow the trigger conditions.
2. **Add `disable-model-invocation: true`** — For manual-only invocation.

### Claude doesn't see all skills

Skill descriptions are loaded into context. If you have many skills, they may exceed the character budget (2% of context window, fallback 16,000 chars total).

- Check: Run `/context` to see if skills are being excluded.
- Fix: Keep descriptions concise and keyword-rich. Override with `SLASH_COMMAND_TOOL_CHAR_BUDGET` env var if needed.

### Subagent skill returns nothing useful

The skill probably contains guidelines without a concrete task. Add explicit instructions: "Do X, then return Y."

### Arguments not being substituted

- Verify `$ARGUMENTS`, `$N`, or `$ARGUMENTS[N]` appears in the skill content.
- If none appear, arguments are appended as `ARGUMENTS: <value>` at the end (automatic fallback).
- Arguments are space-delimited. Spaces within an argument may cause unexpected splitting.

---

## Related Documentation

- **Skills:** https://code.claude.com/docs/en/skills
- **Subagents:** https://code.claude.com/docs/en/sub-agents
- **Hooks:** https://code.claude.com/docs/en/hooks
- **Plugins:** https://code.claude.com/docs/en/plugins
- **Memory (CLAUDE.md):** https://code.claude.com/docs/en/memory
- **Permissions:** https://code.claude.com/docs/en/permissions
