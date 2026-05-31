import { useQuery } from '@tanstack/react-query'
import { tutorApi, type NudgeParams } from '@/api/tutor'

export function useTutorNudges(params: NudgeParams) {
  return useQuery({
    queryKey: ['tutor-nudges', params.context, params.topicId, params.moduleId, params.score],
    queryFn: async () => {
      const { data } = await tutorApi.getNudges(params)
      return data.nudges
    },
  })
}
