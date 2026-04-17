import apiClient from './client'
import type {
  CodingChallenge,
  CodingEvaluation,
  CodingSubmissionHistory,
  TopicChallengeForStudent,
} from '@/types/coding'

export const codingApi = {
  // Returns the student's current AI challenge for this topic (generates or reuses).
  // Falls back to a cloned catalogue challenge if Ollama fails.
  getForTopic: (topicId: number) =>
    apiClient.get<TopicChallengeForStudent>(`/coding/topic/${topicId}`),

  regenerateForTopic: (topicId: number) =>
    apiClient.post<TopicChallengeForStudent>(`/coding/topic/${topicId}/regenerate`),

  getChallenge: (challengeId: number) =>
    apiClient.get<CodingChallenge>(`/coding/challenge/${challengeId}`),

  submitCode: (challengeId: number, code: string) =>
    apiClient.post<CodingEvaluation>(`/coding/challenge/${challengeId}/submit`, { code }),

  getHistory: (challengeId: number) =>
    apiClient.get<CodingSubmissionHistory[]>(`/coding/challenge/${challengeId}/history`),

  getBest: (challengeId: number) =>
    apiClient.get<CodingSubmissionHistory | null>(`/coding/challenge/${challengeId}/best`),
}
