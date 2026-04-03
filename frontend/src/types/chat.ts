export interface ChatSession {
  id: string
  title: string
  created_at: string
  last_message_at: string
}

export interface ChatSource {
  content_preview: string
  document_name: string
  similarity: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources: ChatSource[] | null
  created_at: string
}

export interface ChatMessageResponse {
  message_id: string
  role: 'assistant'
  content: string
  sources: ChatSource[] | null
  created_at: string
}

export interface ChatRemainingResponse {
  remaining: number
  limit: number
}
