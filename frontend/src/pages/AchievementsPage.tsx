import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Trophy } from 'lucide-react'
import { achievementsApi } from '@/api/achievements'
import { SkeletonCard } from '@/components/common/Skeleton'
import AchievementCard from '@/components/achievements/AchievementCard'
import EmptyState from '@/components/common/EmptyState'

export default function AchievementsPage() {
  const { data: achievements, isLoading } = useQuery({
    queryKey: ['achievements'],
    queryFn: () => achievementsApi.list().then((r) => r.data),
  })

  const earned = achievements?.filter((a) => a.is_earned).length ?? 0
  const total = achievements?.length ?? 0

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 p-4 sm:p-6">
        {Array.from({ length: 8 }).map((_, i) => (
          <SkeletonCard key={i} className="h-40" />
        ))}
      </div>
    )
  }

  if (earned === 0) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6">
        <div className="mb-8">
          <span className="heritage-accent-bar mb-3" aria-hidden="true" />
          <h1 className="text-2xl sm:text-3xl font-extrabold text-institutional-700 dark:text-institutional-100">Logros e Insignias</h1>
          <p className="text-muted-foreground mt-1">
            {earned} de {total} logros obtenidos
          </p>
        </div>
        <EmptyState
          icon={Trophy}
          title="Tus logros aparecerán aquí"
          description="Completa módulos, mantén tu racha de estudio y obtén logros desbloqueables."
          action={
            <Link
              to="/modules"
              className="inline-flex items-center justify-center min-h-[44px] px-6 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-colors"
            >
              Ir a módulos
            </Link>
          }
        />
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6">
      <div className="mb-8">
        <span className="heritage-accent-bar mb-3" aria-hidden="true" />
        <h1 className="text-2xl sm:text-3xl font-extrabold text-institutional-700 dark:text-institutional-100">Logros e Insignias</h1>
        <p className="text-muted-foreground mt-1">
          {earned} de {total} logros obtenidos
        </p>
      </div>

      {/* Earned */}
      {earned > 0 && (
        <div className="mb-8">
          <h2 className="font-semibold text-foreground mb-4">Obtenidos</h2>
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
          <h2 className="font-semibold text-foreground mb-4">Por desbloquear</h2>
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
