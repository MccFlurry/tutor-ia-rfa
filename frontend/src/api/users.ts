import apiClient from './client'
import type { User } from '@/types/auth'
import type { UserLevelResponse, ReassessmentProposal } from '@/types/user_level'

export const usersApi = {
  getMe: () => apiClient.get<User>('/users/me'),

  updateMe: (data: { full_name?: string; avatar_url?: string }) =>
    apiClient.put<User>('/users/me', data),

  changePassword: (data: { current_password: string; new_password: string }) =>
    apiClient.put('/users/me/password', data),

  getLevel: () => apiClient.get<UserLevelResponse>('/users/me/level'),

  getReassessmentProposal: () =>
    apiClient.get<ReassessmentProposal>('/users/me/reassessment'),

  confirmReassessment: (accept: boolean) =>
    apiClient.post<UserLevelResponse>('/users/me/reassess', { accept }),
}
