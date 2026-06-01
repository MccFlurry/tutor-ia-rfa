import { CheckCircle2, XCircle, Trophy, RotateCcw, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { QuizSubmitResponse } from '@/types/quiz'

interface QuizResultsProps {
  result: QuizSubmitResponse
  onRetry: () => void
  onBack: () => void
}

export default function QuizResults({ result, onRetry, onBack }: QuizResultsProps) {
  const passed = result.is_passed

  return (
    <div className="space-y-6">
      {/* Score card — green when passed, calm neutral (not harsh red) when not yet */}
      <div
        className={cn(
          'rounded-xl p-8 text-center border-2',
          passed
            ? 'bg-success/10 border-success/30'
            : 'bg-muted/60 border-border'
        )}
      >
        <div className="mb-3">
          {passed ? (
            <Trophy className="w-12 h-12 text-success mx-auto" aria-hidden="true" />
          ) : (
            <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto" aria-hidden="true" />
          )}
        </div>
        <p className={cn('text-4xl font-bold mb-1', passed ? 'text-success' : 'text-foreground')}>
          {result.score}%
        </p>
        <p className={cn('text-sm font-medium', passed ? 'text-success' : 'text-muted-foreground')}>
          {passed
            ? '¡Aprobaste la autoevaluación!'
            : 'Aún no alcanzas el 60%. Repasa el contenido e inténtalo de nuevo.'}
        </p>
      </div>

      {/* Feedback per question — shows every option, marks the correct one and your pick */}
      <div className="space-y-4">
        <h3 className="font-semibold text-foreground">Revisión de respuestas</h3>
        {result.feedback.map((item, i) => (
          <div key={item.question_id} className="rounded-lg border border-border p-4">
            <p className="text-sm font-medium text-foreground mb-3 flex items-start gap-2">
              {item.is_correct ? (
                <CheckCircle2 className="w-5 h-5 text-success mt-0.5 shrink-0" aria-hidden="true" />
              ) : (
                <XCircle className="w-5 h-5 text-destructive mt-0.5 shrink-0" aria-hidden="true" />
              )}
              <span>
                {i + 1}. {item.question_text}
              </span>
            </p>

            <ul className="space-y-1.5">
              {item.options.map((option, oi) => {
                const isCorrect = oi === item.correct_index
                const isChosen = oi === item.selected_index
                return (
                  <li
                    key={oi}
                    className={cn(
                      'flex items-center gap-2 rounded-md border px-3 py-2 text-sm',
                      isCorrect
                        ? 'border-success/40 bg-success/10 text-foreground'
                        : isChosen
                          ? 'border-destructive/40 bg-destructive/10 text-foreground'
                          : 'border-border text-muted-foreground'
                    )}
                  >
                    {isCorrect ? (
                      <CheckCircle2 className="w-4 h-4 text-success shrink-0" aria-hidden="true" />
                    ) : isChosen ? (
                      <XCircle className="w-4 h-4 text-destructive shrink-0" aria-hidden="true" />
                    ) : (
                      <span className="w-4 h-4 shrink-0" aria-hidden="true" />
                    )}
                    <span className="flex-1 break-words">{option}</span>
                    {isCorrect && (
                      <span className="shrink-0 text-xs font-semibold text-success">Correcta</span>
                    )}
                    {isChosen && !isCorrect && (
                      <span className="shrink-0 text-xs font-semibold text-destructive">Tu respuesta</span>
                    )}
                  </li>
                )
              })}
            </ul>

            {item.selected_index < 0 && (
              <p className="mt-2 text-xs text-muted-foreground">No respondiste esta pregunta.</p>
            )}
            {item.explanation && (
              <p className="mt-2 rounded bg-muted/50 px-2 py-1.5 text-xs text-muted-foreground">
                {item.explanation}
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Actions — on a miss, retry is the primary so the next attempt is the obvious step */}
      <div className="flex flex-col sm:flex-row gap-3">
        {passed ? (
          <>
            <Button onClick={onBack}>Volver al tema</Button>
            <Button onClick={onRetry} variant="outline">
              <RotateCcw className="w-4 h-4 mr-2" aria-hidden="true" />
              Intentar con nuevas preguntas
            </Button>
          </>
        ) : (
          <>
            <Button onClick={onRetry}>
              <RotateCcw className="w-4 h-4 mr-2" aria-hidden="true" />
              Intentar de nuevo
            </Button>
            <Button onClick={onBack} variant="outline">
              Volver al tema
            </Button>
          </>
        )}
      </div>
    </div>
  )
}
