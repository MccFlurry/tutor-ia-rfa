import apiClient from './client'
import type {
  ChatSession,
  ChatMessage,
  ChatMessageResponse,
  ChatRemainingResponse,
} from '@/types/chat'

export const chatApi = {
  listSessions: () =>
    apiClient.get<ChatSession[]>('/chat/sessions'),

  createSession: () =>
    apiClient.post<ChatSession>('/chat/sessions'),

  deleteSession: (sessionId: string) =>
    apiClient.delete<{ message: string }>(`/chat/sessions/${sessionId}`),

  getMessages: (sessionId: string) =>
    apiClient.get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`),

  sendMessage: (sessionId: string, content: string) =>
    apiClient.post<ChatMessageResponse>(`/chat/sessions/${sessionId}/message`, {
      content,
    }),

  getRemaining: () =>
    apiClient.get<ChatRemainingResponse>('/chat/remaining'),
}
