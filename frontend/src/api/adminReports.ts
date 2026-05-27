import apiClient from './client'
import type {
  StudentRow,
  StudentDetail,
  AIReport,
  CohortAIReport,
} from '@/types/adminReports'

export const adminReportsApi = {
  listStudents: () => apiClient.get<StudentRow[]>('/admin/students'),

  getDetail: (userId: string) =>
    apiClient.get<StudentDetail>(`/admin/students/${userId}`),

  generateReport: (userId: string) =>
    apiClient.post<AIReport>(`/admin/students/${userId}/ai-report`),

  generateCohortReport: (userIds: string[]) =>
    apiClient.post<CohortAIReport>('/admin/students/cohort/ai-report', {
      user_ids: userIds,
    }),
}
