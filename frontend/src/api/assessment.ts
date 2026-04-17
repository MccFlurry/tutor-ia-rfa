import apiClient from './client'
import type {
  AssessmentStartResponse,
  AssessmentSubmitResponse,
} from '@/types/assessment'

export const assessmentApi = {
  start: () => apiClient.post<AssessmentStartResponse>('/assessment/start'),

  submit: (session_id: string, answers: Record<string, number>) =>
    apiClient.post<AssessmentSubmitResponse>('/assessment/submit', {
      session_id,
      answers,
    }),
}
