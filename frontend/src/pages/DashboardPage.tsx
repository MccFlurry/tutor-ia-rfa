import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Trophy, BookOpen, Sparkles, PlayCircle } from 'lucide-react'
import { dashboardApi } from '@/api/dashboard'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { StudentLevel } from '@/types/assessment'

const LEVEL_LABEL: Record<StudentLevel, string> = {
  beginner: 'Principiante',
  intermediate: 'Intermedio',
  advanced: 'Avanzado',
}

const LEVEL_STYLE: Record<StudentLevel, string> = {
  beginner:     'bg-gray-100 text-gray-700 border-gray-300',
  intermediate: 'bg-primary-50 text-primary-800 border-primary-200',
  advanced:     'bg-heritage-50 text-heritage-700 border-heritage-200',
}

export default function DashboardPage() {
  const navigate = useNavigate()

  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dashboardApi.get().then((r) => r.data),
  })

  if (isLoading || !data) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6">
        <Skeleton className="h-8 w-60 mb-2" />
        <Skeleton className="h-5 w-96 mb-8" />
        <Skeleton className="h-32 mb-8" />
        <div className="grid grid-cols-3 gap-4 mb-8">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
      </div>
    )
  }

  const firstName = data.user_name.split(' ')[0]
  const pct = Math.round(data.overall_progress_pct)

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      {/* Greeting + level badge */}
      <div className="flex items-start justify-between flex-wrap gap-4 mb-8">
        <div>
          <span className="heritage-accent-bar mb-3" aria-hidden="true" />
          <h2 className="text-2xl sm:text-3xl font-extrabold text-institutional-700 mb-1">
            ¡Hola de nuevo, {firstName}!
          </h2>
          <p className="text-gray-600">
            Bienvenido al Sistema de Tutoría Inteligente para Aplicaciones Móviles.
          </p>
        </div>
        {data.user_level && (
          <span
            className={cn(
              'inline-flex items-center gap-1.5 text-sm font-semibold px-3 py-1.5 rounded-full border shadow-brand-sm',
              LEVEL_STYLE[data.user_level]
            )}
          >
            <Sparkles className="w-4 h-4" aria-hidden="true" />
            Tu nivel: {LEVEL_LABEL[data.user_level]}
          </span>
        )}
      </div>

      {/* Hero: continue last topic */}
      {data.last_accessed_topic && !data.last_accessed_topic.is_completed && (
        <section
          aria-labelledby="hero-resume"
          className="relative bg-brand-hero text-white rounded-2xl p-6 sm:p-7 mb-8 shadow-brand-lg overflow-hidden"
        >
          <div className="absolute -top-16 -right-16 w-56 h-56 rounded-full bg-heritage-500/15 blur-3xl" aria-hidden="true" />
          <div className="absolute bottom-0 left-0 h-1 w-full bg-heritage-accent" aria-hidden="true" />
          <div className="relative flex items-center justify-between flex-wrap gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-xs text-primary-200 mb-1 flex items-center gap-1 uppercase tracking-wider font-semibold">
                <PlayCircle className="w-4 h-4" aria-hidden="true" />
                Continuar donde lo dejaste
              </p>
              <h3 id="hero-resume" className="font-extrabold text-lg sm:text-xl truncate">
                {data.last_accessed_topic.topic_title}
              </h3>
              <p className="text-sm text-primary-100 mt-1">
                {data.last_accessed_topic.module_title}
              </p>
            </div>
            <Button
              variant="secondary"
              size="lg"
              className="bg-white text-institutional-700 hover:bg-heritage-50 shadow-brand-md"
              onClick={() => navigate(`/topics/${data.last_accessed_topic!.topic_id}`)}
            >
              Retomar
              <ArrowRight className="w-4 h-4 ml-2" aria-hidden="true" />
            </Button>
          </div>
        </section>
      )}

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6 mb-8">
        <article className="bg-white rounded-xl border border-gray-200 shadow-brand-sm p-6">
          <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold">
            Progreso general
          </p>
          <p className="text-3xl font-extrabold text-institutional-700 mt-2 tabular-nums">
            {pct}<span className="text-xl text-gray-400">%</span>
          </p>
          <Progress value={pct} className="h-2 mt-3" />
        </article>
        <article className="bg-white rounded-xl border border-gray-200 shadow-brand-sm p-6">
          <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold">
            Lecciones completadas
          </p>
          <p className="text-3xl font-extrabold text-gray-900 mt-2 tabular-nums">
            {data.total_topics_completed}
            <span className="text-base font-medium text-gray-400">
              {' / '}
              {data.total_topics}
            </span>
          </p>
        </article>
        <article className="bg-white rounded-xl border border-gray-200 shadow-brand-sm p-6">
          <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold">
            Logros recientes
          </p>
          <p className="text-3xl font-extrabold text-heritage-600 mt-2 tabular-nums">
            {data.recent_achievements.length}
          </p>
        </article>
      </div>

      {/* Recommended modules */}
      {data.recommended_modules.length > 0 && (
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">
              Recomendaciones para ti
            </h3>
            <Button variant="ghost" size="sm" onClick={() => navigate('/modules')}>
              <BookOpen className="w-4 h-4 mr-1" /> Ver todos
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {data.recommended_modules.map((m) => (
              <button
                key={m.id}
                onClick={() => navigate(`/modules/${m.id}`)}
                className="text-left bg-white rounded-xl border border-gray-200 p-5 hover:border-primary-400 hover:shadow-sm transition"
              >
                <div
                  className="w-10 h-10 rounded-lg mb-3 flex items-center justify-center text-white font-bold"
                  style={{ backgroundColor: m.color_hex }}
                >
                  {m.title[0]}
                </div>
                <h4 className="font-semibold text-gray-900 text-sm mb-1">
                  {m.title}
                </h4>
                <p className="text-xs text-gray-500 mb-3 line-clamp-2">
                  {m.reason}
                </p>
                <Progress value={m.progress_pct} className="h-1.5" />
                <p className="text-xs text-gray-400 mt-1">
                  {Math.round(m.progress_pct)}% completado
                </p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Recent achievements */}
      {data.recent_achievements.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <Trophy className="w-4 h-4 text-amber-500" /> Logros recientes
            </h3>
            <Button variant="ghost" size="sm" onClick={() => navigate('/achievements')}>
              Ver todos
            </Button>
          </div>
          <div className="flex gap-3 flex-wrap">
            {data.recent_achievements.map((a) => (
              <div
                key={a.id}
                className="flex items-center gap-3 px-4 py-2 rounded-lg border"
                style={{ borderColor: a.badge_color, backgroundColor: a.badge_color + '15' }}
              >
                <span className="text-2xl">{a.badge_emoji}</span>
                <span className="text-sm font-medium text-gray-800">{a.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
