import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useThemeStore } from './themeStore'

const STORAGE_KEY = 'tutor-rfa.theme'

function freshStore(initialPref: 'light' | 'dark' | 'system' = 'system') {
  // Wipe DOM + storage so the store reads a known state on import.
  document.documentElement.classList.remove('dark')
  window.localStorage.clear()
  window.localStorage.setItem(STORAGE_KEY, initialPref)
  useThemeStore.setState({ pref: initialPref, isDark: false })
}

describe('useThemeStore', () => {
  beforeEach(() => {
    freshStore('system')
  })

  it('setPref("dark") adds the dark class and stores pref', () => {
    useThemeStore.getState().setPref('dark')
    expect(useThemeStore.getState().pref).toBe('dark')
    expect(useThemeStore.getState().isDark).toBe(true)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('dark')
  })

  it('setPref("light") removes the dark class', () => {
    document.documentElement.classList.add('dark')
    useThemeStore.getState().setPref('light')
    expect(useThemeStore.getState().isDark).toBe(false)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('setPref("system") follows matchMedia result', () => {
    vi.spyOn(window, 'matchMedia').mockReturnValue({
      matches: true,
      media: '(prefers-color-scheme: dark)',
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    } as unknown as MediaQueryList)

    useThemeStore.getState().setPref('system')
    expect(useThemeStore.getState().isDark).toBe(true)
  })

  it('init() returns a cleanup fn', () => {
    const cleanup = useThemeStore.getState().init()
    expect(typeof cleanup).toBe('function')
    cleanup()
  })
})
