const ACTIVE_SESSION_KEY = 'geneva.activeSessionId'

export function getActiveSessionId(): string | null {
  return localStorage.getItem(ACTIVE_SESSION_KEY)
}

export function setActiveSessionId(sessionId: string | null): void {
  if (sessionId) {
    localStorage.setItem(ACTIVE_SESSION_KEY, sessionId)
  } else {
    localStorage.removeItem(ACTIVE_SESSION_KEY)
  }
}
