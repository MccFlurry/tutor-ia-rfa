export interface QuizQuestion {
  id: string
  question_text: string
  options: string[]
}

export interface QuizGenerateResponse {
  session_id: string
  questions: QuizQuestion[]
}

export interface QuizFeedbackItem {
  question_id: string
  question_text: string
  selected_index: number
  correct_index: number
  is_correct: boolean
  explanation: string | null
}

export interface QuizSubmitResponse {
  score: number
  is_passed: boolean
  feedback: QuizFeedbackItem[]
  attempt_id: number
}

export interface QuizAttemptHistory {
  attempted_at: string
  score: number
  is_passed: boolean
}
