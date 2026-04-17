import { useQuery } from '@tanstack/react-query'
import { modulesApi } from '@/api/modules'
import ModuleCard from '@/components/modules/ModuleCard'
import { Skeleton } from '@/components/ui/skeleton'

export default function ModulesPage() {
  const { data: modules, isLoading } = useQuery({
    queryKey: ['modules'],
    queryFn: () => modulesApi.list().then((r) => r.data),
  })

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 sm:px-6">
      <header className="mb-8">
        <span className="heritage-accent-bar mb-3" aria-hidden="true" />
        <h1 className="text-2xl sm:text-3xl font-extrabold text-institutional-700">
          Módulos del Curso
        </h1>
        <p className="text-gray-600 mt-1">
          Curso de Aplicaciones Móviles · IESTP "República Federal de Alemania" · Chiclayo
        </p>
      </header>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-56 rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {modules?.map((module) => (
            <ModuleCard key={module.id} module={module} />
          ))}
        </div>
      )}
    </div>
  )
}
