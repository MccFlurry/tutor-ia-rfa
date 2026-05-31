export type NudgeTone = 'info' | 'success' | 'warning' | 'encourage'

export interface Nudge {
  id: string
  tone: NudgeTone
  icon: string
  title: string
  message: string
  cta_label?: string | null
  cta_route?: string | null
}

export interface NudgeResponse {
  nudges: Nudge[]
}

export type NudgeContext =
  | 'dashboard'
  | 'topic'
  | 'module'
  | 'quiz_result'
  | 'coding_result'
  | 'assessment_result'
