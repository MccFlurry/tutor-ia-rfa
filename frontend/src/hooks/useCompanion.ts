import { useQuery } from '@tanstack/react-query'
import { tutorApi } from '@/api/tutor'

export function useCompanion() {
  return useQuery({
    queryKey: ['tutor-companion'],
    queryFn: async () => {
      const { data } = await tutorApi.getCompanion()
      return data
    },
    // staleTime 0: el backend invalida su caché Redis al completar tema/quiz/
    // coding, así cada montaje trae el diagnóstico fresco (la request es liviana,
    // Redis absorbe el costo).
    staleTime: 0,
    refetchOnWindowFocus: false,
  })
}
