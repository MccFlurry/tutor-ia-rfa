import apiClient from './client'
import type { DashboardResponse } from '@/types/dashboard'

export const dashboardApi = {
  get: () => apiClient.get<DashboardResponse>('/dashboard'),
}
