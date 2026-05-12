export interface ModuleProgressItem {
  id: number
  title: string
  pct: number
  completed: number
  total: number
}

export interface ProgressData {
  overall_pct: number
  total_time_seconds: number
  topics_completed: number
  quiz_avg_score: number | null
  modules: ModuleProgressItem[]
}

export interface ActivityItem {
  type: string
  description: string
  timestamp: string
}

export interface StreakResponse {
  current_streak: number
  longest_streak: number
  last_active_date: string | null
}
