import { BookOpen } from 'lucide-react'
import ResourceCard from './ResourceCard'
import { useResources } from '@/hooks/useResources'
import type { LearningResource } from '@/types/resource'

interface Props {
  moduleId?: number
  topicId?: number
  title?: string
  headingLevel?: 2 | 3 | 4
  resources?: LearningResource[]
}

export default function ResourceList({ moduleId, topicId, title = 'Recursos para reforzar', headingLevel = 2, resources: resourcesProp }: Props) {
  const { data: fetched } = useResources({ moduleId, topicId, enabled: !resourcesProp })
  const resources = resourcesProp ?? fetched
  if (!resources || resources.length === 0) return null
  const Heading = (`h${headingLevel}`) as 'h2' | 'h3' | 'h4'
  return (
    <section aria-label={title} className="space-y-2 mb-8">
      <Heading className="flex items-center gap-2 text-sm font-semibold text-foreground">
        <BookOpen className="h-4 w-4 text-primary" aria-hidden="true" />
        {title}
      </Heading>
      <div className="grid gap-2 sm:grid-cols-2">
        {resources.map((r) => (
          <ResourceCard key={r.id} resource={r} />
        ))}
      </div>
    </section>
  )
}
