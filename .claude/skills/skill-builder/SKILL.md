---
name: skill-builder
description: Use when creating new skills from scratch, improving or iterating existing
  skills with eval testing, auditing skill quality, or optimizing skill descriptions
  for better auto-triggering. The complete end-to-end workflow for Claude Code skill
  development — design → build → eval → optimize.
---

# Skill Builder

## Mode Detection

Auto-detect from context. If ambiguous, ask: "สร้างใหม่ หรือ ปรับปรุงของเดิม?"

| Mode | Trigger signals | Read first |
|------|-----------------|------------|
| **Build** | "create a skill", "new skill for X", "make a skill that..." | `references/design.md` |
| **Improve** | "improve this skill", "this skill isn't working", existing SKILL.md provided | `references/eval-loop.md` |
| **Audit** | "audit", "review this skill", "check this skill against best practices" | `references/audit.md` |
| **Optimize** | "optimize description", "fix triggering", "it's not auto-triggering" | `references/description-opt.md` |

## Standard Workflow (Build Mode)

**Design → Build → Eval → Optimize Description → Package**

- Bundle Skills and skills with side effects: never skip Eval
- Simple skills: offer Eval — Bond can say "skip" to ship immediately
- Description optimization always comes last, after content is stable

## Reference Index

| File | Contents | When to read |
|------|----------|--------------|
| `references/design.md` | Discovery interview, Bundle Skill Gate, build phases, templates | Build mode |
| `references/audit.md` | Audit checklists (Frontmatter / Content / Integration / Quality / Bundle) | Audit mode |
| `references/frontmatter.md` | All frontmatter fields, advanced patterns, troubleshooting, invocation control | Any frontmatter question |
| `references/eval-loop.md` | Running evals, grading, benchmarking, eval viewer, iteration loop | After writing a skill |
| `references/description-opt.md` | Description optimization loop (run_loop.py), trigger eval queries | After skill content is stable |
| `references/schemas.md` | JSON schemas for evals.json, grading.json, benchmark.json | During eval setup |

## What Is a Skill?

Skills live in `.claude/skills/[name]/SKILL.md`. They load only when invoked — via `/name` or when Claude auto-detects the need. CLAUDE.md rules always apply on top. Full technical reference → `references/frontmatter.md`

## Global Rules

- Never propose changes to a skill you haven't read
- Run discovery interview before writing anything (Build mode) — skip rounds the user already answered
- Eval is the quality gate: always offer it; never force it when Bond says skip
- Zero dead files — only create supporting files that SKILL.md explicitly references
- Description is the primary trigger mechanism — optimize it last, after content is stable
