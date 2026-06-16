import { useQuery } from '@tanstack/react-query'
import { resourcesApi } from '@/api/resources'

export function useRecommendedResources(params: { moduleId?: number; topicId?: number }) {
  const hasId = params.moduleId != null || params.topicId != null
  return useQuery({
    queryKey: ['resources-recommended', params.moduleId, params.topicId],
    queryFn: async () => {
      const { data } = await resourcesApi.recommended(params)
      return data
    },
    enabled: hasId,
    staleTime: 60_000,
  })
}
