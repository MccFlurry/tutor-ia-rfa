import apiClient from './client'
import type { Achievement } from '@/types/achievement'

export const achievementsApi = {
  list: () =>
    apiClient.get<Achievement[]>('/achievements'),
}
