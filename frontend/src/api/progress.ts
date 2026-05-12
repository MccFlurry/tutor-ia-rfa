import apiClient from './client'
import type { ProgressData, ActivityItem, StreakResponse } from '@/types/progress'

export const progressApi = {
  get: () =>
    apiClient.get<ProgressData>('/progress'),

  getActivity: () =>
    apiClient.get<ActivityItem[]>('/progress/activity'),

  getStreak: () =>
    apiClient.get<StreakResponse>('/progress/streak'),
}
