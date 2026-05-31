import apiClient from './client'
import type { LearningResource } from '@/types/resource'

export const resourcesApi = {
  list: (params: { moduleId?: number; topicId?: number }) =>
    apiClient.get<LearningResource[]>('/resources', {
      params: { module_id: params.moduleId, topic_id: params.topicId },
    }),
}
