import apiClient from './client'
import type { Module, ModuleDetail } from '@/types/module'

export const modulesApi = {
  list: () =>
    apiClient.get<Module[]>('/modules'),

  get: (id: number) =>
    apiClient.get<ModuleDetail>(`/modules/${id}`),
}
