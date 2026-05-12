import { CheckCircle2, XCircle, Trophy, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { QuizSubmitResponse } from '@/types/quiz'

interface QuizResultsProps {
  result: QuizSubmitResponse
  onRetry: () => void
  onBack: () => void
}

export default function QuizResults({ result, onRetry, onBack }: QuizResultsProps) {
  return (
    <div className="space-y-6">
      {/* Score card */}
      <div
        className={cn(
          'rounded-xl p-8 text-center',
          result.is_passed
            ? 'bg-success/10 border-2 border-success/30'
            : 'bg-destructive/10 border-2 border-destructive/30'
        )}
      >
        <div className="mb-3">
          {result.is_passed ? (
            <Trophy className="w-12 h-12 text-success mx-auto" />
          ) : (
            <XCircle className="w-12 h-12 text-destructive mx-auto" />
          )}
        </div>
        <p className={cn(
          'text-4xl font-bold mb-1',
          result.is_passed ? 'text-success' : 'text-destructive'
        )}>
          {result.score}%
        </p>
        <p className={cn(
          'text-sm font-medium',
          result.is_passed ? 'text-success' : 'text-destructive'
        )}>
          {result.is_passed
            ? '¡Aprobaste la autoevaluación!'
            : 'No alcanzaste el puntaje mínimo (60%)'}
        </p>
      </div>

      {/* Feedback per question */}
      <div className="space-y-4">
        <h3 className="font-semibold text-foreground">Revisión de respuestas</h3>
        {result.feedback.map((item, i) => (
          <div
            key={item.question_id}
            className={cn(
              'rounded-lg border p-4',
              item.is_correct
                ? 'bg-success/10 border-success/30'
                : 'bg-destructive/10 border-destructive/30'
            )}
          >
            <div className="flex items-start gap-3">
              {item.is_correct ? (
                <CheckCircle2 className="w-5 h-5 text-success mt-0.5 shrink-0" />
              ) : (
                <XCircle className="w-5 h-5 text-destructive mt-0.5 shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground mb-1">
                  {i + 1}. {item.question_text}
                </p>
                {!item.is_correct && (
                  <p className="text-xs text-destructive mb-1">
                    Tu respuesta: {item.selected_index >= 0 ? `Opción ${item.selected_index + 1}` : 'Sin responder'}
                  </p>
                )}
                {item.explanation && (
                  <p className="text-xs text-muted-foreground mt-1 bg-card/60 rounded px-2 py-1">
                    {item.explanation}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <Button onClick={onRetry} variant="outline">
          <RotateCcw className="w-4 h-4 mr-2" />
          {result.is_passed ? 'Intentar con nuevas preguntas' : 'Intentar de nuevo'}
        </Button>
        <Button onClick={onBack}>
          Volver al tema
        </Button>
      </div>
    </div>
  )
}
