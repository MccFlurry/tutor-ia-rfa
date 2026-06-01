const STORAGE_PREFIX = 'tutor-rfa.coding-draft.'
// Coding effort is valuable and there is no server-side session to race, so keep
// drafts for a week. They're cleared naturally when overwritten or expired.
const TTL_MS = 7 * 24 * 60 * 60 * 1000

interface PersistedCodeDraft {
  code: string
  savedAt: number
}

function keyFor(challengeId: number | string): string {
  return `${STORAGE_PREFIX}${challengeId}`
}

export function loadCodeDraft(challengeId: number | string): string | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(keyFor(challengeId))
    if (!raw) return null
    const parsed = JSON.parse(raw) as PersistedCodeDraft
    if (typeof parsed.code !== 'string' || !parsed.savedAt) {
      window.localStorage.removeItem(keyFor(challengeId))
      return null
    }
    if (Date.now() - parsed.savedAt > TTL_MS) {
      window.localStorage.removeItem(keyFor(challengeId))
      return null
    }
    return parsed.code
  } catch {
    return null
  }
}

export function saveCodeDraft(challengeId: number | string, code: string): void {
  if (typeof window === 'undefined') return
  try {
    const payload: PersistedCodeDraft = { code, savedAt: Date.now() }
    window.localStorage.setItem(keyFor(challengeId), JSON.stringify(payload))
  } catch {
    // localStorage full or disabled — best-effort persistence
  }
}

export function clearCodeDraft(challengeId: number | string): void {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.removeItem(keyFor(challengeId))
  } catch {
    // ignore
  }
}
