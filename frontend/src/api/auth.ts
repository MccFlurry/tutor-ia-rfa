import apiClient from './client'
import type { AuthResponse, LoginRequest, RegisterRequest, TokenResponse, MessageResponse } from '@/types/auth'

export const authApi = {
  register: (data: RegisterRequest) =>
    apiClient.post<AuthResponse>('/auth/register', data),

  login: (data: LoginRequest) =>
    apiClient.post<AuthResponse>('/auth/login', data),

  refresh: (refresh_token: string) =>
    apiClient.post<TokenResponse>('/auth/refresh', { refresh_token }),

  logout: (refresh_token: string) =>
    apiClient.post<MessageResponse>('/auth/logout', { refresh_token }),
}
