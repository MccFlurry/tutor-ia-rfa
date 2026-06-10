import { useNavigate } from 'react-router-dom'
import { ArrowRight, BookOpen, MapPin } from 'lucide-react'
import { Button } from '@/components/ui/button'
import DiagnosticChips from './DiagnosticChips'
import ResourceCard from '@/components/resources/ResourceCard'
import type { CompanionResponse } from '@/types/companion'

/**
 * Panel «Tu ruta» (Fase 5): posición del estudiante, diagnóstico del módulo
 * actual y recursos curados. Reemplaza al hero del Dashboard cuando el
 * endpoint /tutor/companion responde; si no, el hero clásico queda como
 * fallback (degradación silenciosa).
 */
export default function CompanionPanel({ data }: { data: CompanionResponse }) {
  const navigate = useNavigate()
  const { position, diagnostic, greeting, resources } = data
  if (!position || !diagnostic) return null
  const pct = Math.round(position.progress_pct)

  return (
    <>
      <section
        aria-labelledby="companion-heading"
        className="relative bg-brand-hero text-white rounded-2xl p-6 sm:p-7 mb-6 shadow-brand-lg overflow-hidden"
      >
        <div className="absolute -top-16 -right-16 w-56 h-56 rounded-full bg-heritage-500/15 blur-3xl" aria-hidden="true" />
        <div className="absolute bottom-0 left-0 h-1 w-full bg-heritage-accent" aria-hidden="true" />
        <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-xs text-primary-200 mb-1 flex items-center gap-1 uppercase tracking-wider font-semibold">
              <MapPin className="w-4 h-4" aria-hidden="true" />
              {position.course_completed ? 'Curso completado' : 'Tu módulo actual'}
            </p>
            <h2 id="companion-heading" className="font-extrabold text-lg sm:text-xl break-words line-clamp-2">
              {position.module_title}
            </h2>
            <p className="text-sm text-primary-100 mt-1 break-words">{greeting}</p>
            <div className="mt-3 max-w-xs">
              <div className="h-1.5 w-full rounded-full bg-white/20 overflow-hidden">
                <div className="h-full bg-heritage-accent transition-all" style={{ width: `${pct}%` }} />
              </div>
              <p className="text-xs text-primary-200 mt-1">
                {position.topics_done} de {position.topics_total} temas · {pct}%
              </p>
            </div>
          </div>
          <Button
            variant="secondary"
            size="lg"
            className="bg-white text-institutional-700 hover:bg-heritage-50 dark:bg-white dark:text-institutional-700 dark:hover:bg-heritage-50 shadow-brand-md w-full sm:w-auto shrink-0"
            onClick={() => navigate(diagnostic.next_action.route)}
          >
            {diagnostic.next_action.label}
            <ArrowRight className="w-4 h-4 ml-2" aria-hidden="true" />
          </Button>
        </div>
      </section>

      <DiagnosticChips diagnostic={diagnostic} className="mb-6" />

      {resources.length > 0 && (
        <section aria-label="Recursos de tu módulo actual" className="space-y-2 mb-8">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <BookOpen className="h-4 w-4 text-primary" aria-hidden="true" />
            Recursos de tu módulo actual
          </h3>
          <div className="grid gap-2 sm:grid-cols-2">
            {resources.map((r) => (
              <ResourceCard key={r.id} resource={r} />
            ))}
          </div>
        </section>
      )}
    </>
  )
}
