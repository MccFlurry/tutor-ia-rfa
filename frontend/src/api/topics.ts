import apiClient from './client'
import type { Topic, TopicVisitResponse, TopicCompleteResponse, TopicTimeResponse } from '@/types/topic'

export const topicsApi = {
  get: (id: number) =>
    apiClient.get<Topic>(`/topics/${id}`),

  visit: (id: number) =>
    apiClient.post<TopicVisitResponse>(`/topics/${id}/visit`),

  complete: (id: number) =>
    apiClient.post<TopicCompleteResponse>(`/topics/${id}/complete`),

  trackTime: (id: number, seconds: number) =>
    apiClient.post<TopicTimeResponse>(`/topics/${id}/time`, { seconds }),
}
