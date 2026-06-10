import apiClient from './client'
import type { NudgeResponse, NudgeContext } from '@/types/tutor'
import type { CompanionResponse } from '@/types/companion'

export interface NudgeParams {
  context: NudgeContext
  topicId?: number
  moduleId?: number
  score?: number
}

export const tutorApi = {
  getNudges: (p: NudgeParams) =>
    apiClient.get<NudgeResponse>('/tutor/nudges', {
      params: {
        context: p.context,
        topic_id: p.topicId,
        module_id: p.moduleId,
        score: p.score,
      },
    }),
  getCompanion: () => apiClient.get<CompanionResponse>('/tutor/companion'),
}
