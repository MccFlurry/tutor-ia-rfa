export interface Module {
  id: number
  title: string
  description: string | null
  order_index: number
  icon_name: string | null
  color_hex: string
  total_topics: number
  completed_topics: number
  progress_pct: number
  is_locked: boolean
}

export interface TopicBrief {
  id: number
  title: string
  order_index: number
  estimated_minutes: number
  has_quiz: boolean
  has_coding_challenge: boolean
  status: 'not_started' | 'in_progress' | 'completed'
}

export interface ModuleDetail {
  id: number
  title: string
  description: string | null
  order_index: number
  icon_name: string | null
  color_hex: string
  total_topics: number
  completed_topics: number
  progress_pct: number
  topics: TopicBrief[]
}
