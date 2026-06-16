import { BookOpen, Sparkles } from 'lucide-react'
import ResourceCard from './ResourceCard'
import { useRecommendedResources } from '@/hooks/useRecommendedResources'

const LEVEL_LABEL: Record<string, string> = {
  beginner: 'principiante',
  intermediate: 'intermedio',
  advanced: 'avanzado',
}

interface Props {
  moduleId?: number
  topicId?: number
  title?: string
  headingLevel?: 2 | 3 | 4
}

export default function RecommendedResources({
  moduleId,
  topicId,
  title = 'Recomendado para ti',
  headingLevel = 2,
}: Props) {
  const { data } = useRecommendedResources({ moduleId, topicId })
  if (!data || data.recommendations.length === 0) return null
  const Heading = (`h${headingLevel}`) as 'h2' | 'h3' | 'h4'

  return (
    <section aria-label={title} className="space-y-2 mb-8">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Heading className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <BookOpen className="h-4 w-4 text-primary" aria-hidden="true" />
          {title}
        </Heading>
        {data.ai_ranked && (
          <span className="inline-flex items-center gap-1 rounded-full bg-heritage-100 text-heritage-700 dark:bg-heritage-700/20 dark:text-heritage-200 px-2 py-0.5 text-[11px] font-medium">
            <Sparkles className="h-3 w-3" aria-hidden="true" />
            Recomendado por IA · nivel {LEVEL_LABEL[data.level] ?? data.level}
          </span>
        )}
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {data.recommendations.map((r) => (
          <div key={r.id} className="space-y-1">
            <ResourceCard resource={r} />
            {data.ai_ranked && r.reason && (
              <p className="flex items-start gap-1 pl-1 text-xs text-muted-foreground">
                <Sparkles className="mt-0.5 h-3 w-3 shrink-0" aria-hidden="true" />
                <span>{r.reason}</span>
              </p>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
