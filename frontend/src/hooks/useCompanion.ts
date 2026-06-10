import { useQuery } from '@tanstack/react-query'
import { tutorApi } from '@/api/tutor'

export function useCompanion() {
  return useQuery({
    queryKey: ['tutor-companion'],
    queryFn: async () => {
      const { data } = await tutorApi.getCompanion()
      return data
    },
    // 60s alineado con el TTL Redis del backend. La frescura inmediata tras
    // acciones del estudiante viene de invalidateQueries(['tutor-companion'])
    // en las mutaciones (quiz/topic/coding/nivel), no de staleTime 0.
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  })
}
