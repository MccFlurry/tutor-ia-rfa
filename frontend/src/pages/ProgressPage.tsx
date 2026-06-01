import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { BarChart3, Clock, BookOpen, Trophy, Activity, TrendingUp, CheckCircle2, FileQuestion, HelpCircle } from 'lucide-react'
import { progressApi } from '@/api/progress'
import { achievementsApi } from '@/api/achievements'
import { Progress } from '@/components/ui/progress'
import Skeleton from '@/components/common/Skeleton'
import AchievementCard from '@/components/achievements/AchievementCard'
import PageHeader from '@/components/common/PageHeader'
import StatCard from '@/components/common/StatCard'
import EmptyState from '@/components/common/EmptyState'

function formatTime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const mins = Math.floor(seconds / 60)
  if (mins < 60) return `${mins} min`
  const hours = Math.floor(mins / 60)
  const remainMins = mins % 60
  return `${hours}h ${remainMins}m`
}

export default function ProgressPage() {
  const { data: progress, isLoading: loadingProgress } = useQuery({
    queryKey: ['progress'],
    queryFn: () => progressApi.get().then((r) => r.data),
  })

  const { data: achievements, isLoading: loadingAchievements } = useQuery({
    queryKey: ['achievements'],
    queryFn: () => achievementsApi.list().then((r) => r.data),
  })

  const { data: activity } = useQuery({
    queryKey: ['activity'],
    queryFn: () => progressApi.getActivity().then((r) => r.data),
  })

  const isLoading = loadingProgress || loadingAchievements

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6 p-4 sm:p-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} variant="card" className="h-24" />
          ))}
        </div>
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} variant="rect" className="h-12 w-full" />
          ))}
        </div>
      </div>
    )
  }

  const earnedCount = achievements?.filter((a) => a.is_earned).length ?? 0

  // Empty state: no topics completed yet
  if (progress && progress.topics_completed === 0) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6">
        <PageHeader
          title="Mi Progreso"
          subtitle="Avance, tiempo invertido y desempeño por módulo."
        />
        <EmptyState
          icon={TrendingUp}
          title="Tu progreso aparecerá aquí"
          description="Cuando completes temas, verás tu avance por módulo, tiempo de estudio y logros."
          action={
            <Link
              to="/modules"
              className="inline-flex items-center justify-center min-h-[44px] px-6 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-colors"
            >
              Explorar módulos
            </Link>
          }
        />
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6">
      <PageHeader
        title="Mi Progreso"
        subtitle="Avance, tiempo invertido y desempeño por módulo."
      />

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Progreso general"
          value={`${Math.round(progress?.overall_pct ?? 0)}%`}
          icon={BarChart3}
          accent="primary"
        />
        <StatCard
          label="Temas completados"
          value={progress?.topics_completed ?? 0}
          icon={BookOpen}
          accent="success"
        />
        <StatCard
          label="Promedio en quizzes"
          value={
            progress?.quiz_avg_score != null
              ? `${Math.round(progress.quiz_avg_score)}%`
              : '—'
          }
          icon={Trophy}
          accent="info"
        />
        <StatCard
          label="Tiempo total"
          value={formatTime(progress?.total_time_seconds ?? 0)}
          icon={Clock}
          accent="info"
        />
      </div>

      {/* Progress per module */}
      <section
        aria-labelledby="modules-progress-heading"
        className="bg-card rounded-xl border border-border p-4 sm:p-6 mb-8"
      >
        <h2
          id="modules-progress-heading"
          className="font-semibold text-foreground mb-4"
        >
          Progreso por módulo
        </h2>
        <div className="space-y-4">
          {progress?.modules.map((mod) => (
            <div key={mod.id}>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-0.5 sm:gap-2 mb-1.5">
                <span className="text-sm font-medium text-foreground sm:truncate sm:pr-4">
                  {mod.title}
                </span>
                <span className="text-xs sm:text-sm text-muted-foreground shrink-0 tabular-nums">
                  {mod.completed}/{mod.total} — {Math.round(mod.pct)}%
                </span>
              </div>
              <Progress value={mod.pct} className="h-2.5" aria-label={mod.title} />
            </div>
          ))}
        </div>
      </section>

      {/* Achievements */}
      <section
        aria-labelledby="achievements-heading"
        className="bg-card rounded-xl border border-border p-4 sm:p-6 mb-8"
      >
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-2 mb-4">
          <h2 id="achievements-heading" className="font-semibold text-foreground">
            Logros e Insignias
          </h2>
          <span className="text-sm text-muted-foreground tabular-nums">
            {earnedCount} de {achievements?.length ?? 0} obtenidos
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {achievements?.map((a) => (
            <AchievementCard key={a.id} achievement={a} />
          ))}
        </div>
      </section>

      {/* Activity log */}
      <section
        aria-labelledby="activity-heading"
        className="bg-card rounded-xl border border-border p-4 sm:p-6"
      >
        <h2 id="activity-heading" className="font-semibold text-foreground mb-4">
          Actividad reciente
        </h2>
        {activity && activity.length > 0 ? (
          <div className="space-y-3">
            {activity.map((item, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="mt-0.5 shrink-0">
                  {item.type === 'topic_completed' && (
                    <>
                      <CheckCircle2 className="w-[14px] h-[14px] text-success" aria-hidden="true" />
                      <span className="sr-only">Tema completado</span>
                    </>
                  )}
                  {item.type === 'quiz_passed' && (
                    <>
                      <FileQuestion className="w-[14px] h-[14px] text-info" aria-hidden="true" />
                      <span className="sr-only">Quiz aprobado</span>
                    </>
                  )}
                  {item.type === 'achievement' && (
                    <>
                      <Trophy className="w-[14px] h-[14px] text-heritage-500" aria-hidden="true" />
                      <span className="sr-only">Logro</span>
                    </>
                  )}
                  {item.type !== 'topic_completed' && item.type !== 'quiz_passed' && item.type !== 'achievement' && (
                    <>
                      <HelpCircle className="w-[14px] h-[14px] text-muted-foreground" aria-hidden="true" />
                      <span className="sr-only">Actividad</span>
                    </>
                  )}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-foreground">{item.description}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(item.timestamp).toLocaleDateString('es-PE', {
                      day: 'numeric',
                      month: 'short',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Activity}
            title="Sin actividad reciente"
            description="Tu actividad aparecerá aquí a medida que completes temas, quizzes y logros."
          />
        )}
      </section>
    </div>
  )
}
