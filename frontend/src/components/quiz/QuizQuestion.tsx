import { cn } from '@/lib/utils'
import type { QuizQuestion as QuizQuestionType } from '@/types/quiz'

interface QuizQuestionProps {
  question: QuizQuestionType
  index: number
  total: number
  selectedIndex: number | null
  onSelect: (index: number) => void
  disabled?: boolean
}

export default function QuizQuestion({
  question,
  index,
  total,
  selectedIndex,
  onSelect,
  disabled = false,
}: QuizQuestionProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <p className="text-xs text-gray-400 mb-2">
        Pregunta {index + 1} de {total}
      </p>
      <p className="font-medium text-gray-900 mb-4 text-lg leading-relaxed">
        {question.question_text}
      </p>
      <div className="space-y-2">
        {question.options.map((option, i) => (
          <button
            key={i}
            onClick={() => onSelect(i)}
            disabled={disabled}
            className={cn(
              'w-full text-left px-4 py-3 rounded-lg border-2 transition text-sm',
              selectedIndex === i
                ? 'border-primary-500 bg-primary-50 text-primary-800'
                : 'border-gray-200 hover:border-gray-300 text-gray-700',
              disabled && 'cursor-not-allowed opacity-70'
            )}
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  )
}
