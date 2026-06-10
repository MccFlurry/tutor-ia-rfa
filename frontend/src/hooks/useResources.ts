import { useQuery } from '@tanstack/react-query'
import { resourcesApi } from '@/api/resources'

export function useResources(params: { moduleId?: number; topicId?: number; enabled?: boolean }) {
  const hasId = params.moduleId != null || params.topicId != null
  const enabled = (params.enabled ?? true) && hasId
  return useQuery({
    queryKey: ['resources', params.moduleId, params.topicId],
    queryFn: async () => {
      const { data } = await resourcesApi.list(params)
      return data
    },
    enabled,
    staleTime: 60_000,
  })
}
