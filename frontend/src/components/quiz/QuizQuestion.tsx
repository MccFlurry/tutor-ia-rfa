import { RadioGroup } from '@/components/ui/radio-group'
import OptionRadio from '@/components/common/OptionRadio'
import { cn } from '@/lib/utils'
import type { QuizQuestion as QuizQuestionType } from '@/types/quiz'

interface QuizQuestionProps {
  question: QuizQuestionType
  index: number
  total: number
  selectedIndex: number | null
  onSelect: (index: number) => void
  disabled?: boolean
  /** Highlight as unanswered after a blocked submit. */
  invalid?: boolean
}

export default function QuizQuestion({
  question,
  index,
  total,
  selectedIndex,
  onSelect,
  disabled = false,
  invalid = false,
}: QuizQuestionProps) {
  const groupLabelId = `quiz-q-${question.id}-label`

  return (
    <div
      id={`quiz-q-${question.id}`}
      tabIndex={-1}
      className={cn(
        'bg-card rounded-xl border p-4 sm:p-6 scroll-mt-24 focus:outline-none transition-colors',
        invalid ? 'border-destructive ring-2 ring-destructive/40' : 'border-border'
      )}
    >
      <p className="text-xs text-muted-foreground mb-2">
        Pregunta {index + 1} de {total}
      </p>
      <p
        id={groupLabelId}
        className="font-medium text-foreground mb-4 text-base sm:text-lg leading-relaxed break-words"
      >
        {question.question_text}
      </p>
      <RadioGroup
        value={selectedIndex !== null ? String(selectedIndex) : undefined}
        onValueChange={(val) => onSelect(Number(val))}
        disabled={disabled}
        aria-labelledby={groupLabelId}
        aria-invalid={invalid || undefined}
      >
        {question.options.map((option, i) => (
          <OptionRadio key={i} value={String(i)} disabled={disabled}>
            {option}
          </OptionRadio>
        ))}
      </RadioGroup>
      {invalid && (
        <p className="mt-3 text-xs font-medium text-destructive">
          Selecciona una respuesta para continuar.
        </p>
      )}
    </div>
  )
}
