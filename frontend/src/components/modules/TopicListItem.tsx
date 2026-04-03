import { useNavigate } from 'react-router-dom'
import { CheckCircle2, Circle, Clock, FileQuestion, Code2 } from 'lucide-react'
import type { TopicBrief } from '@/types/module'

interface TopicListItemProps {
  topic: TopicBrief
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="w-5 h-5 text-green-500" />
    case 'in_progress':
      return <Circle className="w-5 h-5 text-blue-500 animate-pulse" />
    default:
      return <Circle className="w-5 h-5 text-gray-300" />
  }
}

export default function TopicListItem({ topic }: TopicListItemProps) {
  const navigate = useNavigate()

  return (
    <button
      onClick={() => navigate(`/topics/${topic.id}`)}
      className="w-full flex items-center gap-4 px-4 py-3 rounded-lg hover:bg-gray-50 transition text-left"
    >
      {getStatusIcon(topic.status)}

      <div className="flex-1 min-w-0">
        <p className="font-medium text-gray-900 text-sm truncate">{topic.title}</p>
        <div className="flex items-center gap-3 mt-0.5">
          <span className="text-xs text-gray-400 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {topic.estimated_minutes} min
          </span>
          {topic.has_quiz && (
            <span className="text-xs text-gray-400 flex items-center gap-1">
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

      <span className="text-gray-300 text-sm">&rsaquo;</span>
    </button>
  )
}
