import type { Project, ProjectSource, ProjectSourcePreview, SessionSummary, Todo } from '@/types'

import { jsonFetch } from './core'

export async function fetchProjects(): Promise<Project[]> {
  const data = await jsonFetch<{ projects?: Project[] }>("/api/projects")
  return data.projects ?? []
}

export async function createProject(
  name: string,
  description = "",
  options: Partial<Pick<Project, "color" | "context_md" | "pinned">> = {},
): Promise<Project> {
  const data = await jsonFetch<{ project: Project }>("/api/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description, ...options }),
  })
  return data.project
}

export async function fetchProject(id: string): Promise<Project> {
  const data = await jsonFetch<{ project: Project }>(`/api/projects/${encodeURIComponent(id)}`)
  return data.project
}

export async function fetchProjectSessions(projectId: string): Promise<SessionSummary[]> {
  const data = await jsonFetch<{ sessions?: SessionSummary[] }>(
    `/api/projects/${encodeURIComponent(projectId)}/sessions`,
  )
  return data.sessions ?? []
}

export async function fetchProjectSources(projectId: string): Promise<ProjectSource[]> {
  const data = await jsonFetch<{ sources?: ProjectSource[] }>(
    `/api/projects/${encodeURIComponent(projectId)}/sources`,
  )
  return data.sources ?? []
}

export async function fetchProjectSourcePreview(projectId: string): Promise<ProjectSourcePreview> {
  return jsonFetch<ProjectSourcePreview>(
    `/api/projects/${encodeURIComponent(projectId)}/sources/context-preview`,
  )
}

export async function addProjectTextSource(
  projectId: string,
  data: {
    source_type: "text" | "markdown" | "url"
    title?: string
    content?: string
    url?: string
  },
): Promise<ProjectSource> {
  const response = await jsonFetch<{ source: ProjectSource }>(
    `/api/projects/${encodeURIComponent(projectId)}/sources`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  )
  return response.source
}

export async function updateProjectSource(
  projectId: string,
  sourceId: string,
  data: Partial<Pick<ProjectSource, "title" | "include_policy" | "parse_status" | "parse_error">>,
): Promise<ProjectSource> {
  const response = await jsonFetch<{ source: ProjectSource }>(
    `/api/projects/${encodeURIComponent(projectId)}/sources/${encodeURIComponent(sourceId)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  )
  return response.source
}

export async function deleteProjectSource(projectId: string, sourceId: string): Promise<void> {
  await jsonFetch<{ ok: boolean }>(
    `/api/projects/${encodeURIComponent(projectId)}/sources/${encodeURIComponent(sourceId)}`,
    {
      method: "DELETE",
    },
  )
}

export async function updateProject(
  id: string,
  data: Partial<Pick<Project, "name" | "description" | "context_md" | "color" | "pinned">>,
): Promise<Project> {
  const response = await jsonFetch<{ project: Project }>(`/api/projects/${encodeURIComponent(id)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
  return response.project
}

export async function archiveProject(id: string): Promise<void> {
  await jsonFetch<{ ok: boolean }>(`/api/projects/${encodeURIComponent(id)}/archive`, {
    method: "POST",
  })
}

export async function deleteProject(id: string): Promise<void> {
  await jsonFetch<{ ok: boolean }>(`/api/projects/${encodeURIComponent(id)}`, {
    method: "DELETE",
  })
}

export async function addTodo(projectId: string, text: string): Promise<Todo> {
  const data = await jsonFetch<{ todo: Todo }>(`/api/projects/${encodeURIComponent(projectId)}/todos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  })
  return data.todo
}

export async function toggleTodo(projectId: string, todoId: string, done?: boolean): Promise<Todo | null> {
  const data = await jsonFetch<{ ok: boolean; todo?: Todo }>(
    `/api/projects/${encodeURIComponent(projectId)}/todos/${encodeURIComponent(todoId)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(done === undefined ? { toggle: true } : { done }),
    },
  )
  return data.todo ?? null
}

export async function updateTodoText(projectId: string, todoId: string, text: string): Promise<Todo | null> {
  const data = await jsonFetch<{ ok: boolean; todo?: Todo }>(
    `/api/projects/${encodeURIComponent(projectId)}/todos/${encodeURIComponent(todoId)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    },
  )
  return data.todo ?? null
}

export async function deleteTodo(projectId: string, todoId: string): Promise<void> {
  await jsonFetch<{ ok: boolean }>(
    `/api/projects/${encodeURIComponent(projectId)}/todos/${encodeURIComponent(todoId)}`,
    {
      method: "DELETE",
    },
  )
}

export async function associateSession(projectId: string, sessionId: string): Promise<void> {
  await jsonFetch<{ ok: boolean }>(`/api/projects/${encodeURIComponent(projectId)}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  })
}
