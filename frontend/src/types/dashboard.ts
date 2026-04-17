import type { StudentLevel } from './assessment'

export interface LastAccessedTopic {
  topic_id: number
  topic_title: string
  module_id: number
  module_title: string
  last_accessed_at: string
  is_completed: boolean
}

export interface RecommendedModule {
  id: number
  title: string
  description: string | null
  icon_name: string | null
  color_hex: string
  progress_pct: number
  reason: string
}

export interface RecentAchievement {
  id: number
  name: string
  badge_emoji: string
  badge_color: string
  earned_at: string
}

export interface DashboardResponse {
  user_name: string
  user_level: StudentLevel | null
  overall_progress_pct: number
  total_topics_completed: number
  total_topics: number
  last_accessed_topic: LastAccessedTopic | null
  recommended_modules: RecommendedModule[]
  recent_achievements: RecentAchievement[]
}
