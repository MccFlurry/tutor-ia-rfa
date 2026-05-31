import { BookOpen } from 'lucide-react'
import ResourceCard from './ResourceCard'
import { useResources } from '@/hooks/useResources'

interface Props {
  moduleId?: number
  topicId?: number
  title?: string
}

export default function ResourceList({ moduleId, topicId, title = 'Recursos para reforzar' }: Props) {
  const { data: resources } = useResources({ moduleId, topicId })
  if (!resources || resources.length === 0) return null
  return (
    <section aria-label={title} className="space-y-2">
      <h2 className="flex items-center gap-2 text-sm font-semibold text-foreground">
        <BookOpen className="h-4 w-4 text-primary" aria-hidden="true" />
        {title}
      </h2>
      <div className="grid gap-2 sm:grid-cols-2">
        {resources.map((r) => (
          <ResourceCard key={r.id} resource={r} />
        ))}
      </div>
    </section>
  )
}
