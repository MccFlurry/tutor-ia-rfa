import { useQuery } from '@tanstack/react-query'
import { BarChart3, Clock, BookOpen, Trophy } from 'lucide-react'
import { progressApi } from '@/api/progress'
import { achievementsApi } from '@/api/achievements'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import AchievementCard from '@/components/achievements/AchievementCard'

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
      <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6 space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Skeleton className="h-28 rounded-xl" />
          <Skeleton className="h-28 rounded-xl" />
          <Skeleton className="h-28 rounded-xl" />
        </div>
        <Skeleton className="h-64 rounded-xl" />
      </div>
    )
  }

  const earnedCount = achievements?.filter((a) => a.is_earned).length ?? 0

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6">
      <header className="mb-6">
        <span className="heritage-accent-bar mb-3" aria-hidden="true" />
        <h1 className="text-2xl sm:text-3xl font-extrabold text-institutional-700">Mi Progreso</h1>
        <p className="text-gray-600 mt-1">Avance, tiempo invertido y desempeño por módulo.</p>
      </header>

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 bg-primary-100 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-primary-600" />
            </div>
            <p className="text-sm text-gray-500">Progreso general</p>
          </div>
          <p className="text-3xl font-bold text-primary-600">
            {Math.round(progress?.overall_pct ?? 0)}%
          </p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 bg-green-100 rounded-lg flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-sm text-gray-500">Temas completados</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {progress?.topics_completed ?? 0}
          </p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 bg-amber-100 rounded-lg flex items-center justify-center">
              <Trophy className="w-5 h-5 text-amber-600" />
            </div>
            <p className="text-sm text-gray-500">Promedio en quizzes</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {progress?.quiz_avg_score != null
              ? `${Math.round(progress.quiz_avg_score)}%`
              : '—'}
          </p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 bg-violet-100 rounded-lg flex items-center justify-center">
              <Clock className="w-5 h-5 text-violet-600" />
            </div>
            <p className="text-sm text-gray-500">Tiempo total</p>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {formatTime(progress?.total_time_seconds ?? 0)}
          </p>
        </div>
      </div>

      {/* Progress per module */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
        <h2 className="font-semibold text-gray-900 mb-4">Progreso por módulo</h2>
        <div className="space-y-4">
          {progress?.modules.map((mod) => (
            <div key={mod.id}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-medium text-gray-700 truncate pr-4">
                  {mod.title}
                </span>
                <span className="text-sm text-gray-500 shrink-0">
                  {mod.completed}/{mod.total} — {Math.round(mod.pct)}%
                </span>
              </div>
              <Progress value={mod.pct} className="h-2.5" />
            </div>
          ))}
        </div>
      </div>

      {/* Achievements */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">Logros e Insignias</h2>
          <span className="text-sm text-gray-500">
            {earnedCount} de {achievements?.length ?? 0} obtenidos
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {achievements?.map((a) => (
            <AchievementCard key={a.id} achievement={a} />
          ))}
        </div>
      </div>

      {/* Activity log */}
      {activity && activity.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Actividad reciente</h2>
          <div className="space-y-3">
            {activity.map((item, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className={`w-2 h-2 rounded-full mt-2 shrink-0 ${
                  item.type === 'topic_completed'
                    ? 'bg-green-500'
                    : item.type === 'quiz_passed'
                    ? 'bg-blue-500'
                    : 'bg-red-400'
                }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-700">{item.description}</p>
                  <p className="text-xs text-gray-400">
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
        </div>
      )}
    </div>
  )
}
