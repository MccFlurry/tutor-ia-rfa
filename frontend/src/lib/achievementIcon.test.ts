import { describe, expect, it } from 'vitest'
import { Rocket, Trophy, Flame, Bot, Star, GraduationCap, Zap, Award } from 'lucide-react'
import { getAchievementIcon } from './achievementIcon'

describe('getAchievementIcon', () => {
  it.each([
    ['first_topic', Rocket],
    ['module_completed', Trophy],
    ['streak_days', Flame],
    ['chat_messages', Bot],
    ['quiz_perfect', Star],
    ['course_completed', GraduationCap],
  ])('maps %s → expected icon', (type, expected) => {
    const icon = getAchievementIcon({
      condition_type: type as any,
      condition_module_id: null,
    })
    expect(icon).toBe(expected)
  })

  it('uses Zap for module-specific completions', () => {
    const icon = getAchievementIcon({
      condition_type: 'module_completed',
      condition_module_id: 2,
    })
    expect(icon).toBe(Zap)
  })

  it('falls back to Award for unknown condition types', () => {
    const icon = getAchievementIcon({
      condition_type: 'unknown-future-type' as any,
      condition_module_id: null,
    })
    expect(icon).toBe(Award)
  })
})
