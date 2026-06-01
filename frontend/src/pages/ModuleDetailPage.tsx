import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ChevronRight, Lock } from 'lucide-react'
import * as LucideIcons from 'lucide-react'
import { modulesApi } from '@/api/modules'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import TopicListItem from '@/components/modules/TopicListItem'

function getIcon(iconName: string | null) {
  if (!iconName) return LucideIcons.BookOpen
  const pascal = iconName
    .split('-')
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join('')
  return (LucideIcons as Record<string, any>)[pascal] || LucideIcons.BookOpen
}

export default function ModuleDetailPage() {
  const { id } = useParams<{ id: string }>()

  const { data: module, isLoading } = useQuery({
    queryKey: ['module', id],
    queryFn: () => modulesApi.get(Number(id)).then((r) => r.data),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96" />
        <Skeleton className="h-48 w-full rounded-xl" />
      </div>
    )
  }

  if (!module) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <p className="text-muted-foreground">Módulo no encontrado.</p>
      </div>
    )
  }

  const Icon = getIcon(module.icon_name)

  // Locked module: the backend withholds the topics. Explain why instead of
  // exposing an enterable (but empty) content list — no dead-ends.
  if (module.is_locked) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6">
        <nav className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground mb-6">
          <Link to="/modules" className="hover:text-primary-600 dark:hover:text-primary-400 transition">
            Módulos
          </Link>
          <ChevronRight className="w-4 h-4 shrink-0" />
          <span className="text-foreground font-medium break-words">{module.title}</span>
        </nav>

        <div className="bg-card rounded-xl border border-border p-6 sm:p-8 text-center">
          <div className="w-14 h-14 rounded-xl bg-muted flex items-center justify-center mx-auto mb-4">
            <Lock className="w-7 h-7 text-muted-foreground" aria-hidden="true" />
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-foreground mb-2 break-words">
            {module.title}
          </h1>
          <p className="text-sm text-muted-foreground max-w-md mx-auto mb-6">
            Completa el módulo anterior para desbloquear este contenido.
          </p>
          <Link
            to="/modules"
            className="inline-flex items-center justify-center min-h-[44px] px-6 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            Volver a módulos
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6">
      {/* Breadcrumb */}
      <nav className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground mb-6">
        <Link to="/modules" className="hover:text-primary-600 dark:hover:text-primary-400 transition">
          Módulos
        </Link>
        <ChevronRight className="w-4 h-4 shrink-0" />
        <span className="text-foreground font-medium break-words">{module.title}</span>
      </nav>

      {/* Header */}
      <div className="bg-card rounded-xl border border-border p-4 sm:p-6 mb-6">
        <div className="flex items-center gap-3 sm:gap-4 mb-4">
          <div
            className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl flex items-center justify-center shrink-0"
            style={{ backgroundColor: module.color_hex + '20' }}
          >
            <Icon className="w-6 h-6 sm:w-7 sm:h-7" style={{ color: module.color_hex }} />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="text-xl sm:text-2xl font-extrabold text-institutional-700 dark:text-institutional-100 break-words">{module.title}</h1>
            <p className="text-sm text-muted-foreground break-words">{module.description}</p>
          </div>
        </div>
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>{module.completed_topics} de {module.total_topics} temas completados</span>
            <span className="font-medium">{Math.round(module.progress_pct)}%</span>
          </div>
          <Progress value={module.progress_pct} className="h-2.5" />
        </div>
      </div>

      {/* Topics list */}
      <div className="bg-card rounded-xl border border-border divide-y divide-border">
        <div className="px-4 sm:px-6 py-4">
          <h2 className="font-semibold text-foreground">Temas del módulo</h2>
        </div>
        <div className="px-2 py-2">
          {module.topics.map((topic) => (
            <TopicListItem key={topic.id} topic={topic} />
          ))}
          {module.topics.length === 0 && (
            <p className="text-center text-muted-foreground py-8 text-sm">
              No hay temas disponibles.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
