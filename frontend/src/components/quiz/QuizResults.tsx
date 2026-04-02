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
            ? 'bg-green-50 border-2 border-green-200'
            : 'bg-red-50 border-2 border-red-200'
        )}
      >
        <div className="mb-3">
          {result.is_passed ? (
            <Trophy className="w-12 h-12 text-green-500 mx-auto" />
          ) : (
            <XCircle className="w-12 h-12 text-red-400 mx-auto" />
          )}
        </div>
        <p className="text-4xl font-bold mb-1" style={{
          color: result.is_passed ? '#16a34a' : '#dc2626'
        }}>
          {result.score}%
        </p>
        <p className={cn(
          'text-sm font-medium',
          result.is_passed ? 'text-green-700' : 'text-red-700'
        )}>
          {result.is_passed
            ? '¡Aprobaste la autoevaluación!'
            : 'No alcanzaste el puntaje mínimo (60%)'}
        </p>
      </div>

      {/* Feedback per question */}
      <div className="space-y-4">
        <h3 className="font-semibold text-gray-900">Revisión de respuestas</h3>
        {result.feedback.map((item, i) => (
          <div
            key={item.question_id}
            className={cn(
              'rounded-lg border p-4',
              item.is_correct
                ? 'bg-green-50/50 border-green-200'
                : 'bg-red-50/50 border-red-200'
            )}
          >
            <div className="flex items-start gap-3">
              {item.is_correct ? (
                <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
              ) : (
                <XCircle className="w-5 h-5 text-red-400 mt-0.5 shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 mb-1">
                  {i + 1}. {item.question_text}
                </p>
                {!item.is_correct && (
                  <p className="text-xs text-red-600 mb-1">
                    Tu respuesta: {item.selected_index >= 0 ? `Opción ${item.selected_index + 1}` : 'Sin responder'}
                  </p>
                )}
                {item.explanation && (
                  <p className="text-xs text-gray-600 mt-1 bg-white/60 rounded px-2 py-1">
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
