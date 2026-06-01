import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  Trophy,
  Sparkles,
  PlayCircle,
  CheckCircle2,
  BarChart3,
  GraduationCap,
  Flame,
  Signal,
  AlertTriangle,
  RefreshCw,
  HelpCircle,
} from 'lucide-react'
import { dashboardApi } from '@/api/dashboard'
import { progressApi } from '@/api/progress'
import Skeleton, { SkeletonCard } from '@/components/common/Skeleton'
import { Button } from '@/components/ui/button'
import PageHeader from '@/components/common/PageHeader'
import StatCard from '@/components/common/StatCard'
import EmptyState from '@/components/common/EmptyState'
import { getAchievementIcon } from '@/lib/achievementIcon'
import { cn } from '@/lib/utils'
import type { StudentLevel } from '@/types/assessment'
import TutorNudgeList from '@/components/tutor/TutorNudgeList'
import ResourceList from '@/components/resources/ResourceList'

const LEVEL_LABEL: Record<StudentLevel, string> = {
  beginner: 'Principiante',
  intermediate: 'Intermedio',
  advanced: 'Avanzado',
}

const LEVEL_STYLE: Record<StudentLevel, string> = {
  beginner:     'bg-muted text-foreground border-border',
  intermediate: 'bg-primary-50 text-primary-800 border-primary-200 dark:bg-primary/15 dark:text-primary-200 dark:border-primary-700',
  advanced:     'bg-success/10 text-success border-success/30',
}

export default function DashboardPage() {
  const navigate = useNavigate()

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dashboardApi.get().then((r) => r.data),
  })

  const { data: streak, isPending: streakPending } = useQuery({
    queryKey: ['streak'],
    queryFn: () => progressApi.getStreak().then((r) => r.data),
    staleTime: 60 * 1000,
  })

  // Initial load: skeletons that match the real layout (hero + 3-up stats + 3-up recs).
  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8 sm:px-6 lg:px-8 space-y-6">
        <Skeleton variant="card" className="h-32 w-full" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    )
  }

  // Fetch failed: recover gracefully instead of an endless skeleton.
  if (isError || !data) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 sm:px-6">
        <EmptyState
          icon={AlertTriangle}
          tone="error"
          title="No pudimos cargar tu panel"
          description="Hubo un problema al obtener tu progreso. Revisa tu conexión e inténtalo de nuevo."
          action={
            <Button onClick={() => refetch()}>
              <RefreshCw className="w-4 h-4 mr-2" aria-hidden="true" />
              Reintentar
            </Button>
          }
        />
      </div>
    )
  }

  const firstName = data.user_name.split(' ')[0]
  const pct = Math.round(data.overall_progress_pct)

  // Empty state: brand-new user with no activity yet
  if (data.total_topics_completed === 0 && !data.last_accessed_topic) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 sm:px-6">
        <PageHeader title={`¡Hola, ${firstName}!`} />
        <EmptyState
          icon={Sparkles}
          title="¡Comencemos tu aprendizaje!"
          description="Aún no has iniciado ningún módulo. Cuando comiences, verás aquí tu progreso, logros y recomendaciones."
          action={
            <Link
              to="/modules"
              className="inline-flex items-center justify-center min-h-[44px] px-6 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-colors"
            >
              Comenzar primer módulo
            </Link>
          }
        />
      </div>
    )
  }

  const levelChip = data.user_level && (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 text-sm font-semibold px-3 py-1.5 rounded-full border shadow-brand-sm',
        LEVEL_STYLE[data.user_level]
      )}
    >
      <Signal className="w-4 h-4" aria-hidden="true" />
      Tu nivel: {LEVEL_LABEL[data.user_level]}
    </span>
  )

  // The hero always offers the next step — it never disappears, even right after
  // a student finishes their last topic (no dead-ends).
  const resume = data.last_accessed_topic
  const nextModule = data.recommended_modules[0]
  const resumeActive = !!resume && !resume.is_completed
  const justCompleted = !!resume && resume.is_completed

  const HeroIcon = resumeActive ? PlayCircle : justCompleted ? CheckCircle2 : PlayCircle
  const heroEyebrow = resumeActive ? 'Continuar donde lo dejaste' : 'Sigue avanzando'
  const heroTitle = resumeActive
    ? resume!.topic_title
    : nextModule
      ? nextModule.title
      : 'Explora los módulos del curso'
  const heroSubtitle = resumeActive
    ? resume!.module_title
    : justCompleted
      ? `Completaste "${resume!.topic_title}". Continúa con tu siguiente paso.`
      : 'Elige un módulo para seguir aprendiendo.'
  const heroCta = resumeActive ? 'Retomar' : 'Continuar'
  const goHero = () => {
    if (resumeActive) return navigate(`/topics/${resume!.topic_id}`)
    if (nextModule) return navigate(`/modules/${nextModule.id}`)
    if (resume) return navigate(`/modules/${resume.module_id}`)
    navigate('/modules')
  }

  // When the hero points at a recommended module (just-completed / no-resume path),
  // drop that module from the grid below so it isn't shown twice.
  const heroModuleId = !resumeActive && nextModule ? nextModule.id : undefined
  const recommendations = heroModuleId
    ? data.recommended_modules.filter((m) => m.id !== heroModuleId)
    : data.recommended_modules

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      <PageHeader
        title={`¡Hola de nuevo, ${firstName}!`}
        subtitle="Bienvenido al Sistema de Tutoría Inteligente para Aplicaciones Móviles."
        actions={levelChip}
      />

      <TutorNudgeList context="dashboard" />

      {/* Hero: the single next step on the path (always present) */}
      <section
        aria-labelledby="hero-resume"
        className="relative bg-brand-hero text-white rounded-2xl p-6 sm:p-7 mb-6 shadow-brand-lg overflow-hidden"
      >
        <div className="absolute -top-16 -right-16 w-56 h-56 rounded-full bg-heritage-500/15 blur-3xl" aria-hidden="true" />
        <div className="absolute bottom-0 left-0 h-1 w-full bg-heritage-accent" aria-hidden="true" />
        <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-xs text-primary-200 mb-1 flex items-center gap-1 uppercase tracking-wider font-semibold">
              <HeroIcon className="w-4 h-4" aria-hidden="true" />
              {heroEyebrow}
            </p>
            <h2 id="hero-resume" className="font-extrabold text-lg sm:text-xl break-words line-clamp-2">
              {heroTitle}
            </h2>
            <p className="text-sm text-primary-100 mt-1 break-words">
              {heroSubtitle}
            </p>
          </div>
          <Button
            variant="secondary"
            size="lg"
            className="bg-white text-institutional-700 hover:bg-heritage-50 dark:bg-white dark:text-institutional-700 dark:hover:bg-heritage-50 shadow-brand-md w-full sm:w-auto shrink-0"
            onClick={goHero}
          >
            {heroCta}
            <ArrowRight className="w-4 h-4 ml-2" aria-hidden="true" />
          </Button>
        </div>
      </section>

      {/* Help pointer: ties the dashboard to the tutor, for students unsure how to continue */}
      <p className="flex flex-wrap items-center justify-center gap-x-1.5 gap-y-1 text-sm text-muted-foreground mb-8">
        <HelpCircle className="w-4 h-4 text-primary" aria-hidden="true" />
        ¿No sabes cómo continuar?{' '}
        <Link
          to="/chat"
          className="font-semibold text-primary rounded hover:underline underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          Pregúntale a tu tutor IA
        </Link>
      </p>

      {/* Stats */}
      <section aria-labelledby="stats-heading" className="mb-8">
        <h2 id="stats-heading" className="font-semibold text-foreground mb-4">
          Tu progreso
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          <StatCard
            label="Progreso general"
            value={
              <>
                {pct}
                <span className="text-xl text-muted-foreground">%</span>
              </>
            }
            icon={BarChart3}
            accent="primary"
            progress={pct}
          />
          <StatCard
            label="Lecciones completadas"
            value={
              <>
                {data.total_topics_completed}
                <span className="text-base font-medium text-muted-foreground">
                  {' / '}
                  {data.total_topics}
                </span>
              </>
            }
            icon={GraduationCap}
            accent="success"
          />
          <StatCard
            label="Racha actual"
            liveValue
            value={
              streakPending ? (
                '—'
              ) : (
                <>
                  {streak?.current_streak ?? 0}
                  <span className="text-base font-medium text-muted-foreground">
                    {' '}
                    {(streak?.current_streak ?? 0) === 1 ? 'día' : 'días'}
                  </span>
                </>
              )
            }
            icon={Flame}
            accent="warning"
            helperText={
              streakPending
                ? undefined
                : (streak?.current_streak ?? 0) === 0
                  ? '¡Empieza tu racha hoy!'
                  : streak && streak.longest_streak > 0
                    ? `Mejor racha: ${streak.longest_streak} ${streak.longest_streak === 1 ? 'día' : 'días'}`
                    : undefined
            }
          />
        </div>
      </section>

      {/* Recommended modules */}
      {recommendations.length > 0 && (
        <section aria-labelledby="recommended-heading" className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 id="recommended-heading" className="font-semibold text-foreground">
              Recomendaciones para ti
            </h2>
            <Button variant="ghost" size="sm" onClick={() => navigate('/modules')}>
              Ver todos
            </Button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {recommendations.map((m) => (
              <button
                key={m.id}
                onClick={() => navigate(`/modules/${m.id}`)}
                style={{ '--module-color': m.color_hex } as React.CSSProperties}
                className="text-left bg-card rounded-xl border border-border p-5
                           hover:border-[color:var(--module-color)] hover:shadow-brand-sm transition
                           focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                <div
                  className="w-10 h-10 rounded-lg mb-3 flex items-center justify-center font-bold
                             bg-[color:var(--module-color)]/12 text-[color:var(--module-color)]
                             ring-1 ring-inset ring-[color:var(--module-color)]/25"
                  aria-hidden="true"
                >
                  {m.title[0]}
                </div>
                <h3 className="font-semibold text-foreground text-sm mb-1">
                  {m.title}
                </h3>
                <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
                  {m.reason}
                </p>
                {m.progress_pct > 0 ? (
                  <>
                    <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full bg-[color:var(--module-color)] transition-all"
                        style={{ width: `${m.progress_pct}%` }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {Math.round(m.progress_pct)}% completado
                    </p>
                  </>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-primary">
                    Empezar
                    <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                  </span>
                )}
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Resources for first recommended module */}
      {data?.recommended_modules?.[0] && (
        <ResourceList moduleId={data.recommended_modules[0].id} title="Recursos recomendados" />
      )}

      {/* Recent achievements */}
      {data.recent_achievements.length > 0 && (
        <section
          aria-labelledby="recent-achievements-heading"
          className="bg-card rounded-xl border border-border p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2
              id="recent-achievements-heading"
              className="font-semibold text-foreground flex items-center gap-2"
            >
              <Trophy className="w-4 h-4 text-heritage-600 dark:text-heritage-400" aria-hidden="true" />
              Logros recientes
            </h2>
            <Button variant="ghost" size="sm" onClick={() => navigate('/achievements')}>
              Ver todos
            </Button>
          </div>
          <div className="flex gap-3 flex-wrap">
            {data.recent_achievements.map((a) => {
              const Icon = getAchievementIcon(a)
              return (
                <div
                  key={a.id}
                  style={{ '--badge-color': a.badge_color } as React.CSSProperties}
                  className="flex items-center gap-2.5 px-3.5 py-2 rounded-lg border
                             border-[color:var(--badge-color)]/30 bg-[color:var(--badge-color)]/10"
                >
                  <Icon
                    className="w-4 h-4 shrink-0"
                    style={{ color: a.badge_color }}
                    aria-hidden="true"
                  />
                  <span className="text-sm font-medium text-foreground">{a.name}</span>
                </div>
              )
            })}
          </div>
        </section>
      )}
    </div>
  )
}
