import apiClient from './client'
import type { LearningResource, RecommendationResponse } from '@/types/resource'

export const resourcesApi = {
  list: (params: { moduleId?: number; topicId?: number }) =>
    apiClient.get<LearningResource[]>('/resources', {
      params: { module_id: params.moduleId, topic_id: params.topicId },
    }),
  recommended: (params: { moduleId?: number; topicId?: number }) =>
    apiClient.get<RecommendationResponse>('/resources/recommended', {
      params: { module_id: params.moduleId, topic_id: params.topicId },
    }),
}
