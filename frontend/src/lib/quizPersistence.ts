import type { QuizQuestion } from '@/types/quiz'

const STORAGE_PREFIX = 'tutor-rfa.quiz-state.'
// Match backend AI quiz session TTL (30 min). Use 25 min on the client so we
// expire before the server does and avoid 410-on-submit races.
const TTL_MS = 25 * 60 * 1000

export interface PersistedQuizState {
  session_id: string
  questions: QuizQuestion[]
  answers: Record<string, number>
  savedAt: number
}

function keyFor(topicId: number | string): string {
  return `${STORAGE_PREFIX}${topicId}`
}

export function loadQuizState(topicId: number | string): PersistedQuizState | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(keyFor(topicId))
    if (!raw) return null
    const parsed = JSON.parse(raw) as PersistedQuizState
    if (!parsed.session_id || !Array.isArray(parsed.questions) || !parsed.savedAt) {
      window.localStorage.removeItem(keyFor(topicId))
      return null
    }
    if (Date.now() - parsed.savedAt > TTL_MS) {
      window.localStorage.removeItem(keyFor(topicId))
      return null
    }
    return parsed
  } catch {
    return null
  }
}

export function saveQuizState(
  topicId: number | string,
  state: Omit<PersistedQuizState, 'savedAt'>
): void {
  if (typeof window === 'undefined') return
  try {
    const payload: PersistedQuizState = { ...state, savedAt: Date.now() }
    window.localStorage.setItem(keyFor(topicId), JSON.stringify(payload))
  } catch {
    // localStorage full or disabled — silent fail; persistence is best-effort
  }
}

export function clearQuizState(topicId: number | string): void {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.removeItem(keyFor(topicId))
  } catch {
    // ignore
  }
}
