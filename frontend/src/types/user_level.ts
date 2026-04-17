import type { StudentLevel } from './assessment'

export interface LevelHistoryEntry {
  level: StudentLevel
  score: number
  changed_at: string
  reason: string
}

export interface UserLevelResponse {
  level: StudentLevel | null
  entry_score: number | null
  assessed_at: string | null
  last_reassessed_at: string | null
  history: LevelHistoryEntry[]
}

export interface ReassessmentProposal {
  should_reassess: boolean
  direction: 'up' | 'down' | null
  current_level: StudentLevel | null
  proposed_level: StudentLevel | null
  reason: string | null
}
