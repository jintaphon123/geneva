import type { SkillMeta } from '@/types'

import { jsonFetch } from './core'

export interface SkillFileNode {
  type: "file" | "dir"
  name: string
  path: string
  children?: SkillFileNode[]
}

export async function fetchSkills(): Promise<{ skills: SkillMeta[]; count: number }> {
  return jsonFetch<{ skills: SkillMeta[]; count: number }>("/api/skills")
}

export async function fetchSkill(name: string): Promise<{ skill: SkillMeta & { system_prompt: string } }> {
  return jsonFetch<{ skill: SkillMeta & { system_prompt: string } }>(
    `/api/skills/${encodeURIComponent(name)}`,
  )
}

export async function createSkill(name: string, content: string): Promise<{ skill: SkillMeta }> {
  return jsonFetch<{ skill: SkillMeta }>("/api/skills", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, content }),
  })
}

export async function updateSkill(name: string, content: string): Promise<{ ok: boolean; skill?: SkillMeta }> {
  return jsonFetch<{ ok: boolean; skill?: SkillMeta }>(`/api/skills/${encodeURIComponent(name)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  })
}

export async function activateSkill(name: string): Promise<{ ok: boolean; skill: SkillMeta }> {
  return jsonFetch<{ ok: boolean; skill: SkillMeta }>(
    `/api/skills/${encodeURIComponent(name)}/activate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note: "Activated from Skill Control Plane" }),
    },
  )
}

export async function setSkillStatus(
  name: string,
  status: "review" | "active" | "disabled" | "archived",
): Promise<{ ok: boolean; skill: SkillMeta }> {
  return jsonFetch<{ ok: boolean; skill: SkillMeta }>(
    `/api/skills/${encodeURIComponent(name)}/status`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    },
  )
}

export async function addSkillEval(
  name: string,
  input: string,
  expected: string,
  status: "pending" | "passed" | "failed" = "passed",
  actual = "",
  notes = "",
): Promise<{ ok: boolean; skill: SkillMeta }> {
  return jsonFetch<{ ok: boolean; skill: SkillMeta }>(
    `/api/skills/${encodeURIComponent(name)}/evals`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input, expected, status, actual, notes }),
    },
  )
}

export async function updateSkillEval(
  name: string,
  evalId: string,
  status: "pending" | "passed" | "failed",
  actual = "",
  notes = "",
): Promise<{ ok: boolean; skill: SkillMeta }> {
  return jsonFetch<{ ok: boolean; skill: SkillMeta }>(
    `/api/skills/${encodeURIComponent(name)}/evals/${encodeURIComponent(evalId)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status, actual, notes }),
    },
  )
}

export async function rollbackSkill(name: string, revisionId: string): Promise<{ ok: boolean; skill: SkillMeta }> {
  return jsonFetch<{ ok: boolean; skill: SkillMeta }>(
    `/api/skills/${encodeURIComponent(name)}/rollback`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ revision_id: revisionId }),
    },
  )
}

export async function submitSkillFeedback(
  name: string,
  score: number,
  outcome: string,
  note = "",
  suggestedChange = "",
): Promise<{ ok: boolean; skill: SkillMeta }> {
  return jsonFetch<{ ok: boolean; skill: SkillMeta }>(
    `/api/skills/${encodeURIComponent(name)}/feedback`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        score,
        outcome,
        note,
        suggested_change: suggestedChange,
      }),
    },
  )
}

export async function deleteSkill(name: string): Promise<{ ok: boolean }> {
  return jsonFetch<{ ok: boolean }>(`/api/skills/${encodeURIComponent(name)}`, {
    method: "DELETE",
  })
}

export async function reloadSkills(): Promise<{ count: number }> {
  return jsonFetch<{ count: number }>("/api/skills/reload", {
    method: "POST",
  })
}

export async function buildSkill(description: string): Promise<{
  skill: SkillMeta
  raw: string
  requires_review?: boolean
}> {
  return jsonFetch<{ skill: SkillMeta; raw: string; requires_review?: boolean }>("/api/skills/build", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description }),
  })
}

export async function importFromMyBrain(mybrainPath?: string): Promise<{
  skills_imported: number
  context_imported: number
  brain_md_created: boolean
  errors: string[]
}> {
  return jsonFetch<{
    skills_imported: number
    context_imported: number
    brain_md_created: boolean
    errors: string[]
  }>("/api/import/mybrain", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mybrain_path: mybrainPath }),
  })
}

export async function fetchSkillFiles(name: string): Promise<{ files: SkillFileNode[] }> {
  return jsonFetch<{ files: SkillFileNode[] }>(`/api/skills/${encodeURIComponent(name)}/files`)
}

export async function fetchSkillFile(
  name: string,
  path: string,
): Promise<{ content: string; path: string; name: string }> {
  return jsonFetch<{ content: string; path: string; name: string }>(
    `/api/skills/${encodeURIComponent(name)}/file?path=${encodeURIComponent(path)}`,
  )
}
