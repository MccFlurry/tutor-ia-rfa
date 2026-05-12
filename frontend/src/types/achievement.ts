export type AchievementConditionType =
  | 'first_topic'
  | 'module_completed'
  | 'streak_days'
  | 'chat_messages'
  | 'quiz_perfect'
  | 'course_completed'

export interface Achievement {
  id: number
  name: string
  description: string
  badge_emoji: string
  badge_color: string
  condition_type: AchievementConditionType | string
  condition_module_id: number | null
  is_earned: boolean
  earned_at: string | null
}
