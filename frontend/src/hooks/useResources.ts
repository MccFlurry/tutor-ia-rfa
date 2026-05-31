import { useQuery } from '@tanstack/react-query'
import { resourcesApi } from '@/api/resources'

export function useResources(params: { moduleId?: number; topicId?: number }) {
  const enabled = params.moduleId != null || params.topicId != null
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
