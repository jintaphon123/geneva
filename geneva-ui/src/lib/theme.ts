export const THEME_MODE_KEY = "geneva.themeMode"
export const THEME_MODE_USER_SET_KEY = "geneva.themeModeUserSet"
export const LEGACY_DARK_MODE_KEY = "geneva.darkMode"
export const GHOST_MODE_KEY = "geneva.ghostMode"

export type ThemeMode = "system" | "light" | "dark"

export function getInitialThemeMode(): ThemeMode {
  const saved = localStorage.getItem(THEME_MODE_KEY)
  const userSet = localStorage.getItem(THEME_MODE_USER_SET_KEY) === "1"
  if (saved === "system" && userSet) return saved
  if (saved === "light" || saved === "dark") return saved
  if (localStorage.getItem(LEGACY_DARK_MODE_KEY) === "1") return "dark"
  return "light"
}

export function getSystemDarkMode(): boolean {
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false
}
