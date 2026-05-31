import { Youtube, BookOpen, FileText, ExternalLink } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { LearningResource, ResourceKind } from '@/types/resource'

const KIND_ICON: Record<ResourceKind, LucideIcon> = {
  video: Youtube,
  book: BookOpen,
  article: FileText,
  doc: FileText,
}

const KIND_LABEL: Record<ResourceKind, string> = {
  video: 'Video',
  book: 'Libro',
  article: 'Artículo',
  doc: 'Documentación',
}

export default function ResourceCard({ resource }: { resource: LearningResource }) {
  const Icon = KIND_ICON[resource.kind] ?? FileText
  return (
    <a
      href={resource.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex items-start gap-3 rounded-lg border border-border bg-card p-3
                 hover:border-primary/40 hover:bg-muted/40 transition-colors
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <Icon className="h-5 w-5 shrink-0 text-primary mt-0.5" aria-hidden="true" />
      <div className="flex-1 min-w-0">
        <p className="font-medium text-foreground flex items-center gap-1">
          <span className="truncate">{resource.title}</span>
          <ExternalLink className="h-3 w-3 shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100" aria-hidden="true" />
        </p>
        <p className="text-xs text-muted-foreground">
          {KIND_LABEL[resource.kind]}
          {resource.author ? ` · ${resource.author}` : ''}
        </p>
        {resource.description && (
          <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{resource.description}</p>
        )}
      </div>
    </a>
  )
}
