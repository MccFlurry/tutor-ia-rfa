import apiClient from './client'
import type {
  TopicChallengesResponse,
  CodingChallenge,
  CodingEvaluation,
  CodingSubmissionHistory,
} from '@/types/coding'

export const codingApi = {
  getChallengesForTopic: (topicId: number) =>
    apiClient.get<TopicChallengesResponse>(`/coding/topic/${topicId}`),

  getChallenge: (challengeId: number) =>
    apiClient.get<CodingChallenge>(`/coding/challenge/${challengeId}`),

  submitCode: (challengeId: number, code: string) =>
    apiClient.post<CodingEvaluation>(`/coding/challenge/${challengeId}/submit`, { code }),

  getHistory: (challengeId: number) =>
    apiClient.get<CodingSubmissionHistory[]>(`/coding/challenge/${challengeId}/history`),

  getBest: (challengeId: number) =>
    apiClient.get<CodingSubmissionHistory | null>(`/coding/challenge/${challengeId}/best`),
}
