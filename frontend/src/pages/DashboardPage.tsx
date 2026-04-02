import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { BookOpen, ArrowRight } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { modulesApi } from '@/api/modules'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const navigate = useNavigate()

  const { data: modules, isLoading } = useQuery({
    queryKey: ['modules'],
    queryFn: () => modulesApi.list().then((r) => r.data),
  })

  // Calculate overall progress
  const totalTopics = modules?.reduce((sum, m) => sum + m.total_topics, 0) ?? 0
  const completedTopics = modules?.reduce((sum, m) => sum + m.completed_topics, 0) ?? 0
  const overallPct = totalTopics > 0 ? Math.round((completedTopics / totalTopics) * 100) : 0

  // Find the first module that is in progress or not started (and not locked)
  const currentModule = modules?.find(
    (m) => !m.is_locked && m.progress_pct < 100
  )

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6">
      {/* Greeting */}
      <h2 className="text-2xl font-bold text-gray-900 mb-1">
        ¡Hola de nuevo, {user?.full_name?.split(' ')[0]}!
      </h2>
      <p className="text-gray-500 mb-8">
        Bienvenido al Sistema de Tutoría Inteligente para Aplicaciones Móviles.
      </p>

      {/* Continue where you left off */}
      {currentModule && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-500 mb-1">Continuar donde lo dejaste</p>
              <h3 className="font-semibold text-gray-900 text-lg">{currentModule.title}</h3>
              <div className="flex items-center gap-3 mt-2">
                <Progress value={currentModule.progress_pct} className="h-2 flex-1 max-w-xs" />
                <span className="text-sm text-gray-500">{Math.round(currentModule.progress_pct)}%</span>
              </div>
            </div>
            <Button onClick={() => navigate(`/modules/${currentModule.id}`)}>
              Continuar
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      )}

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <p className="text-sm text-gray-500">Progreso general</p>
          <p className="text-3xl font-bold text-primary-600 mt-1">{overallPct}%</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <p className="text-sm text-gray-500">Lecciones completadas</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{completedTopics}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <p className="text-sm text-gray-500">Total de módulos</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{modules?.length ?? 0}</p>
        </div>
      </div>

      {/* Module progress overview */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">Progreso por módulo</h3>
          <Button variant="ghost" size="sm" onClick={() => navigate('/modules')}>
            <BookOpen className="w-4 h-4 mr-1" />
            Ver todos
          </Button>
        </div>

        {isLoading ? (
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10" />
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {modules?.map((module) => (
              <div key={module.id} className="flex items-center gap-4">
                <span className="text-sm text-gray-700 w-48 truncate font-medium">
                  {module.order_index}. {module.title}
                </span>
                <Progress value={module.progress_pct} className="h-2 flex-1" />
                <span className="text-xs text-gray-500 w-10 text-right">
                  {Math.round(module.progress_pct)}%
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
