import { useNavigate } from 'react-router-dom'
import { CheckCircle2, Circle, CircleDot, Clock, FileQuestion, Code2, ChevronRight } from 'lucide-react'
import type { TopicBrief } from '@/types/module'

interface TopicListItemProps {
  topic: TopicBrief
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'completed':
      return (
        <>
          <CheckCircle2 className="w-5 h-5 text-success" aria-hidden="true" />
          <span className="sr-only">Completado</span>
        </>
      )
    case 'in_progress':
      return (
        <>
          <CircleDot className="w-5 h-5 text-info motion-safe:animate-pulse" aria-hidden="true" />
          <span className="sr-only">En progreso</span>
        </>
      )
    default:
      return (
        <>
          <Circle className="w-5 h-5 text-muted-foreground" aria-hidden="true" />
          <span className="sr-only">No iniciado</span>
        </>
      )
  }
}

export default function TopicListItem({ topic }: TopicListItemProps) {
  const navigate = useNavigate()

  return (
    <button
      onClick={() => navigate(`/topics/${topic.id}`)}
      className="w-full min-h-[44px] flex items-center gap-3 sm:gap-4 px-3 sm:px-4 py-3 rounded-lg hover:bg-surface-hover transition-colors text-left"
    >
      {getStatusIcon(topic.status)}

      <div className="flex-1 min-w-0">
        <p className="font-medium text-foreground text-sm truncate">{topic.title}</p>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-0.5">
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {topic.estimated_minutes} min
          </span>
          {topic.has_quiz && (
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <FileQuestion className="w-3 h-3" />
              Quiz
            </span>
          )}
          {topic.has_coding_challenge && (
            <span className="text-xs text-primary-500 flex items-center gap-1">
              <Code2 className="w-3 h-3" />
              Desafío de Código
            </span>
          )}
        </div>
      </div>

      <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" aria-hidden="true" />
    </button>
  )
}
