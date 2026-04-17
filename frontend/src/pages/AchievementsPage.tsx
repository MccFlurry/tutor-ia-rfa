import { useQuery } from '@tanstack/react-query'
import { achievementsApi } from '@/api/achievements'
import { Skeleton } from '@/components/ui/skeleton'
import AchievementCard from '@/components/achievements/AchievementCard'

export default function AchievementsPage() {
  const { data: achievements, isLoading } = useQuery({
    queryKey: ['achievements'],
    queryFn: () => achievementsApi.list().then((r) => r.data),
  })

  const earned = achievements?.filter((a) => a.is_earned).length ?? 0
  const total = achievements?.length ?? 0

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6 space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 7 }).map((_, i) => (
            <Skeleton key={i} className="h-36 rounded-xl" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6">
      <div className="mb-8">
        <span className="heritage-accent-bar mb-3" aria-hidden="true" />
        <h1 className="text-2xl sm:text-3xl font-extrabold text-institutional-700">Logros e Insignias</h1>
        <p className="text-gray-600 mt-1">
          {earned} de {total} logros obtenidos
        </p>
      </div>

      {/* Earned */}
      {earned > 0 && (
        <div className="mb-8">
          <h2 className="font-semibold text-gray-900 mb-4">Obtenidos</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {achievements?.filter((a) => a.is_earned).map((a) => (
              <AchievementCard key={a.id} achievement={a} />
            ))}
          </div>
        </div>
      )}

      {/* Locked */}
      {earned < total && (
        <div>
          <h2 className="font-semibold text-gray-900 mb-4">Por desbloquear</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {achievements?.filter((a) => !a.is_earned).map((a) => (
              <AchievementCard key={a.id} achievement={a} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
