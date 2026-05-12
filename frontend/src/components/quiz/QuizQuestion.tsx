import { RadioGroup } from '@/components/ui/radio-group'
import OptionRadio from '@/components/common/OptionRadio'
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
  const groupLabelId = `quiz-q-${question.id}-label`

  return (
    <div className="bg-card rounded-xl border border-border p-6">
      <p className="text-xs text-muted-foreground mb-2">
        Pregunta {index + 1} de {total}
      </p>
      <p
        id={groupLabelId}
        className="font-medium text-foreground mb-4 text-lg leading-relaxed"
      >
        {question.question_text}
      </p>
      <RadioGroup
        value={selectedIndex !== null ? String(selectedIndex) : undefined}
        onValueChange={(val) => onSelect(Number(val))}
        disabled={disabled}
        aria-labelledby={groupLabelId}
      >
        {question.options.map((option, i) => (
          <OptionRadio key={i} value={String(i)} disabled={disabled}>
            {option}
          </OptionRadio>
        ))}
      </RadioGroup>
    </div>
  )
}
