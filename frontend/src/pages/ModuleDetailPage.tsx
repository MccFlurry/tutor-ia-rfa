import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ChevronRight } from 'lucide-react'
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
        <p className="text-gray-500">Módulo no encontrado.</p>
      </div>
    )
  }

  const Icon = getIcon(module.icon_name)

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/modules" className="hover:text-primary-600 transition">
          Módulos
        </Link>
        <ChevronRight className="w-4 h-4" />
        <span className="text-gray-900 font-medium">{module.title}</span>
      </nav>

      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-4 mb-4">
          <div
            className="w-14 h-14 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: module.color_hex + '20' }}
          >
            <Icon className="w-7 h-7" style={{ color: module.color_hex }} />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-institutional-700">{module.title}</h1>
            <p className="text-sm text-gray-500">{module.description}</p>
          </div>
        </div>
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-gray-500">
            <span>{module.completed_topics} de {module.total_topics} temas completados</span>
            <span className="font-medium">{Math.round(module.progress_pct)}%</span>
          </div>
          <Progress value={module.progress_pct} className="h-2.5" />
        </div>
      </div>

      {/* Topics list */}
      <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
        <div className="px-6 py-4">
          <h2 className="font-semibold text-gray-900">Temas del módulo</h2>
        </div>
        <div className="px-2 py-2">
          {module.topics.map((topic) => (
            <TopicListItem key={topic.id} topic={topic} />
          ))}
          {module.topics.length === 0 && (
            <p className="text-center text-gray-400 py-8 text-sm">
              No hay temas disponibles.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
