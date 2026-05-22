import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  clearQuizState,
  loadQuizState,
  saveQuizState,
  type PersistedQuizState,
} from './quizPersistence'

const TOPIC_ID = 42
const STATE: Omit<PersistedQuizState, 'savedAt'> = {
  session_id: 'sess-1',
  questions: [
    { id: 'q0', question_text: '¿X?', options: ['a', 'b', 'c', 'd'] },
  ],
  answers: { q0: 1 },
}

describe('quizPersistence', () => {
  beforeEach(() => {
    window.localStorage.clear()
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-05-21T10:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns null when nothing saved', () => {
    expect(loadQuizState(TOPIC_ID)).toBeNull()
  })

  it('round-trips a saved state', () => {
    saveQuizState(TOPIC_ID, STATE)
    const loaded = loadQuizState(TOPIC_ID)
    expect(loaded).not.toBeNull()
    expect(loaded!.session_id).toBe('sess-1')
    expect(loaded!.answers).toEqual({ q0: 1 })
    expect(loaded!.savedAt).toBeTypeOf('number')
  })

  it('expires stale state past TTL (25 min)', () => {
    saveQuizState(TOPIC_ID, STATE)
    // Jump 26 minutes
    vi.setSystemTime(new Date('2026-05-21T10:26:00Z'))
    expect(loadQuizState(TOPIC_ID)).toBeNull()
  })

  it('clearQuizState removes the entry', () => {
    saveQuizState(TOPIC_ID, STATE)
    clearQuizState(TOPIC_ID)
    expect(loadQuizState(TOPIC_ID)).toBeNull()
  })

  it('ignores malformed json', () => {
    window.localStorage.setItem(`tutor-rfa.quiz-state.${TOPIC_ID}`, '{not-json')
    expect(loadQuizState(TOPIC_ID)).toBeNull()
  })

  it('rejects entries missing required fields', () => {
    window.localStorage.setItem(
      `tutor-rfa.quiz-state.${TOPIC_ID}`,
      JSON.stringify({ answers: {} })
    )
    expect(loadQuizState(TOPIC_ID)).toBeNull()
  })

  it('partitions state per topic id', () => {
    saveQuizState(1, { ...STATE, session_id: 'a' })
    saveQuizState(2, { ...STATE, session_id: 'b' })
    expect(loadQuizState(1)!.session_id).toBe('a')
    expect(loadQuizState(2)!.session_id).toBe('b')
  })
})
