export type Difficulty = 'easy' | 'medium' | 'hard'

export interface AssessmentQuestion {
  id: string
  question_text: string
  options: string[]
  module_id: number
  difficulty: Difficulty
}

export interface AssessmentStartResponse {
  session_id: string
  questions: AssessmentQuestion[]
  source: 'ai' | 'bank'
}

export interface ModuleScoreBreakdown {
  module_id: number
  module_title: string
  correct: number
  total: number
  percentage: number
}

export interface AssessmentSubmitResponse {
  level: StudentLevel
  score: number
  confidence: number
  module_breakdown: ModuleScoreBreakdown[]
  feedback: string
}

export type StudentLevel = 'beginner' | 'intermediate' | 'advanced'
