export interface Achievement {
  id: number
  name: string
  description: string
  badge_emoji: string
  badge_color: string
  is_earned: boolean
  earned_at: string | null
}
