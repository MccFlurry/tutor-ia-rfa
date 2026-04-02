import apiClient from './client'
import type { QuizGenerateResponse, QuizSubmitResponse, QuizAttemptHistory } from '@/types/quiz'

export const quizApi = {
  generate: (topicId: number) =>
    apiClient.get<QuizGenerateResponse>(`/quiz/topic/${topicId}`),

  submit: (topicId: number, sessionId: string, answers: Record<string, number>) =>
    apiClient.post<QuizSubmitResponse>(`/quiz/topic/${topicId}/submit`, {
      session_id: sessionId,
      answers,
    }),

  getHistory: (topicId: number) =>
    apiClient.get<QuizAttemptHistory[]>(`/quiz/topic/${topicId}/history`),
}
