import { create } from 'zustand'

export type ThemePref = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'tutor-rfa.theme'

function getInitialPref(): ThemePref {
  if (typeof window === 'undefined') return 'system'
  const saved = window.localStorage.getItem(STORAGE_KEY)
  if (saved === 'light' || saved === 'dark' || saved === 'system') return saved
  return 'system'
}

function systemPrefersDark(): boolean {
  if (typeof window === 'undefined' || !window.matchMedia) return false
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

function applyClass(isDark: boolean) {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  if (isDark) {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
  root.style.colorScheme = isDark ? 'dark' : 'light'
}

interface ThemeStore {
  pref: ThemePref
  isDark: boolean
  setPref: (p: ThemePref) => void
  /** Initialize: apply current pref + listen to system changes. Returns cleanup. */
  init: () => () => void
}

export const useThemeStore = create<ThemeStore>((set, get) => ({
  pref: getInitialPref(),
  isDark: false,

  setPref: (p) => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, p)
    }
    const isDark = p === 'dark' || (p === 'system' && systemPrefersDark())
    applyClass(isDark)
    set({ pref: p, isDark })
  },

  init: () => {
    const pref = get().pref
    const isDark = pref === 'dark' || (pref === 'system' && systemPrefersDark())
    applyClass(isDark)
    set({ isDark })

    if (typeof window === 'undefined' || !window.matchMedia) return () => {}
    const mql = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e: MediaQueryListEvent) => {
      if (get().pref !== 'system') return
      applyClass(e.matches)
      set({ isDark: e.matches })
    }
    mql.addEventListener('change', handler)
    return () => mql.removeEventListener('change', handler)
  },
}))
