export interface CodingChallenge {
  id: number
  topic_id: number
  title: string
  description: string
  initial_code: string | null
  language: string
  difficulty: 'easy' | 'medium' | 'hard'
  hints: string | null
  order_index: number
}

export interface TopicChallengesResponse {
  topic_id: number
  challenges: CodingChallenge[]
  has_challenges: boolean
}

export interface CodingEvaluation {
  submission_id: number
  score: number
  feedback: string
  strengths: string[] | null
  improvements: string[] | null
}

export interface CodingSubmissionHistory {
  id: number
  code: string
  score: number
  feedback: string
  strengths: string[] | null
  improvements: string[] | null
  submitted_at: string
}
