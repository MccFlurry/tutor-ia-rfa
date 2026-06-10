import type { LearningResource } from './resource'

export interface CompanionPosition {
  module_id: number
  module_title: string
  icon_name: string | null
  color_hex: string | null
  progress_pct: number
  topics_done: number
  topics_total: number
  course_completed: boolean
}

export interface TopicDiagnostic {
  topic_id: number
  title: string
  /** 0-100, null si nunca intentó el quiz */
  best_score: number | null
  attempts: number
}

export type NextActionKind = 'retry_quiz' | 'next_topic' | 'coding_challenge' | 'module'

export interface NextAction {
  kind: NextActionKind
  label: string
  route: string
}

export interface ModuleDiagnostic {
  weak: TopicDiagnostic[]
  practice: TopicDiagnostic[]
  next_action: NextAction
}

export interface CompanionResponse {
  needs_assessment: boolean
  position: CompanionPosition | null
  greeting: string
  diagnostic: ModuleDiagnostic | null
  resources: LearningResource[]
}
