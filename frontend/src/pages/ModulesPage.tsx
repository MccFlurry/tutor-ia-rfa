import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { BookOpen, Lock, AlertTriangle, RefreshCw } from 'lucide-react'
import { modulesApi } from '@/api/modules'
import ModuleCard from '@/components/modules/ModuleCard'
import { SkeletonCard } from '@/components/common/Skeleton'
import PageHeader from '@/components/common/PageHeader'
import EmptyState from '@/components/common/EmptyState'
import { Button } from '@/components/ui/button'

export default function ModulesPage() {
  const { data: modules, isLoading, isError, refetch } = useQuery({
    queryKey: ['modules'],
    queryFn: () => modulesApi.list().then((r) => r.data),
  })

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 sm:px-6">
      <PageHeader
        title="Módulos del Curso"
        subtitle={'Curso de Aplicaciones Móviles · IESTP "República Federal de Alemania" · Chiclayo'}
      />

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} className="h-48" />
          ))}
        </div>
      ) : isError ? (
        <EmptyState
          icon={AlertTriangle}
          tone="error"
          title="No pudimos cargar los módulos"
          description="Hubo un problema al obtener los módulos. Revisa tu conexión e inténtalo de nuevo."
          action={
            <Button onClick={() => refetch()}>
              <RefreshCw className="w-4 h-4 mr-2" aria-hidden="true" />
              Reintentar
            </Button>
          }
        />
      ) : !modules || modules.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="Sin módulos disponibles"
          description="Aún no hay módulos publicados. Vuelve más tarde o contacta al administrador."
        />
      ) : modules.every((m) => m.is_locked) ? (
        <EmptyState
          icon={Lock}
          title="Necesitas completar tu evaluación"
          description="Para desbloquear los módulos, primero realiza la evaluación inicial."
          action={
            <Link
              to="/assessment"
              className="inline-flex items-center justify-center min-h-[44px] px-6 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-colors"
            >
              Ir a evaluación
            </Link>
          }
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {modules.map((module) => (
            <ModuleCard key={module.id} module={module} />
          ))}
        </div>
      )}
    </div>
  )
}
