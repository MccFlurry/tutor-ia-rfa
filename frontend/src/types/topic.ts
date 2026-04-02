export interface TopicModuleInfo {
  id: number
  title: string
}

export interface TopicProgressInfo {
  is_completed: boolean
  time_spent_seconds: number
  first_visited_at: string | null
  completed_at: string | null
}

export interface Topic {
  id: number
  title: string
  content_markdown: string
  video_url: string | null
  estimated_minutes: number
  has_quiz: boolean
  order_index: number
  module: TopicModuleInfo
  progress_info: TopicProgressInfo | null
}

export interface TopicVisitResponse {
  message: string
}

export interface TopicCompleteResponse {
  message: string
  is_completed: boolean
}

export interface TopicTimeResponse {
  message: string
  total_seconds: number
}
