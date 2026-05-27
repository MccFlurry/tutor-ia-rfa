import type { StudentLevel } from './assessment'

export interface StudentRow {
  user_id: string
  full_name: string
  email: string
  level: StudentLevel | null
  entry_score: number | null
  overall_progress_pct: number
  avg_quiz_score: number | null
  avg_coding_score: number | null
  last_activity_at: string | null
  last_location: string | null
  is_active: boolean
}

export interface ModuleProgress {
  module_id: number
  module_title: string
  topics_total: number
  topics_completed: number
  progress_pct: number
  avg_quiz_score: number | null
  avg_coding_score: number | null
}

export interface QuizAttemptRow {
  attempt_id: number
  topic_id: number
  topic_title: string
  score: number
  is_passed: boolean
  attempted_at: string
}

export interface CodingSubmissionRow {
  submission_id: number
  challenge_id: number
  challenge_title: string
  score: number
  submitted_at: string
}

export interface AchievementRow {
  achievement_id: number
  name: string
  badge_emoji: string
  earned_at: string
}

export interface LevelHistoryEntry {
  level: StudentLevel
  score: number
  changed_at: string
  reason: string | null
}

export interface StudentDetail {
  user_id: string
  full_name: string
  email: string
  created_at: string
  is_active: boolean
  level: StudentLevel | null
  entry_score: number | null
  level_history: LevelHistoryEntry[]
  overall_progress_pct: number
  modules: ModuleProgress[]
  recent_quizzes: QuizAttemptRow[]
  recent_coding: CodingSubmissionRow[]
  chat_messages_count: number
  chat_last_at: string | null
  achievements_earned: AchievementRow[]
  total_time_seconds: number
  last_activity_at: string | null
  last_location: string | null
}

export type RiskLevel = 'bajo' | 'medio' | 'alto'

export interface AIReport {
  summary: string
  strengths: string[]
  weaknesses: string[]
  risk_level: RiskLevel
  risk_reason: string
  interventions: string[]
  generated_at: string
  cached: boolean
}

export interface CohortAIReport {
  narrative: string
  top_performers: string[]
  needs_support: string[]
  common_gaps: string[]
  recommendations: string[]
  generated_at: string
  cached: boolean
}
