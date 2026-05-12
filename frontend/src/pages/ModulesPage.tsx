import { useQuery } from '@tanstack/react-query'
import { BookOpen } from 'lucide-react'
import { modulesApi } from '@/api/modules'
import ModuleCard from '@/components/modules/ModuleCard'
import { Skeleton } from '@/components/ui/skeleton'
import PageHeader from '@/components/common/PageHeader'
import EmptyState from '@/components/common/EmptyState'

export default function ModulesPage() {
  const { data: modules, isLoading } = useQuery({
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
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-56 rounded-xl" />
          ))}
        </div>
      ) : !modules || modules.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="Sin módulos disponibles"
          description="Aún no hay módulos publicados. Vuelve más tarde o contacta al administrador."
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
