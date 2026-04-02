import apiClient from './client'
import type { User } from '@/types/auth'

export const usersApi = {
  getMe: () => apiClient.get<User>('/users/me'),

  updateMe: (data: { full_name?: string; avatar_url?: string }) =>
    apiClient.put<User>('/users/me', data),

  changePassword: (data: { current_password: string; new_password: string }) =>
    apiClient.put('/users/me/password', data),
}
