import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Sparkles, ChevronLeft, ChevronRight, CheckCircle2, AlertTriangle, TrendingUp } from 'lucide-react'
import toast from 'react-hot-toast'
import { assessmentApi } from '@/api/assessment'
import { usersApi } from '@/api/users'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import BrandLogo from '@/components/brand/BrandLogo'
import { useAuthStore } from '@/store/authStore'
import type {
  AssessmentStartResponse,
  AssessmentSubmitResponse,
  StudentLevel,
} from '@/types/assessment'

const LEVEL_LABEL: Record<StudentLevel, string> = {
  beginner: 'Principiante',
  intermediate: 'Intermedio',
  advanced: 'Avanzado',
}

const LEVEL_COLOR: Record<StudentLevel, string> = {
  beginner:     'bg-gray-100 text-gray-700 border-gray-300',
  intermediate: 'bg-primary-50 text-primary-800 border-primary-200',
  advanced:     'bg-heritage-50 text-heritage-700 border-heritage-200',
}

const DIFFICULTY_LABEL: Record<string, string> = {
  easy: 'Fácil',
  medium: 'Media',
  hard: 'Difícil',
}

export default function EntryAssessmentPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === 'admin'

  const [session, setSession] = useState<AssessmentStartResponse | null>(null)
  const [currentIdx, setCurrentIdx] = useState(0)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [result, setResult] = useState<AssessmentSubmitResponse | null>(null)

  // Admins bypass entry assessment entirely
  useEffect(() => {
    if (isAdmin) navigate('/admin', { replace: true })
  }, [isAdmin, navigate])

  // Check whether user already has a level → skip assessment
  const { data: levelData, isLoading: isLoadingLevel } = useQuery({
    queryKey: ['my-level'],
    queryFn: () => usersApi.getLevel().then((r) => r.data),
    enabled: !isAdmin,
  })

  useEffect(() => {
    if (levelData?.level) {
      navigate('/dashboard', { replace: true })
    }
  }, [levelData, navigate])

  const startMutation = useMutation({
    mutationFn: () => assessmentApi.start().then((r) => r.data),
    onSuccess: (data) => setSession(data),
    onError: () =>
      toast.error(
        'No se pudo generar la evaluación. El servicio de IA puede no estar disponible.'
      ),
  })

  const submitMutation = useMutation({
    mutationFn: () => {
      if (!session) throw new Error('No session')
      return assessmentApi.submit(session.session_id, answers).then((r) => r.data)
    },
    onSuccess: (data) => {
      setResult(data)
      queryClient.invalidateQueries({ queryKey: ['my-level'] })
    },
    onError: () => toast.error('Error al enviar la evaluación'),
  })

  const handleStart = () => startMutation.mutate()

  const handleSelect = (qid: string, idx: number) =>
    setAnswers((prev) => ({ ...prev, [qid]: idx }))

  const handleNext = () => {
    if (!session) return
    if (currentIdx < session.questions.length - 1) {
      setCurrentIdx((i) => i + 1)
    }
  }

  const handlePrev = () => {
    if (currentIdx > 0) setCurrentIdx((i) => i - 1)
  }

  const handleSubmit = () => {
    if (!session) return
    const unanswered = session.questions.filter((q) => answers[q.id] === undefined)
    if (unanswered.length > 0) {
      toast.error(`Te faltan ${unanswered.length} pregunta(s) por responder`)
      return
    }
    submitMutation.mutate()
  }

  const handleGoDashboard = () => navigate('/dashboard', { replace: true })

  if (isLoadingLevel) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-institutional-50 via-white to-heritage-50">
        <div className="text-gray-500">Cargando...</div>
      </div>
    )
  }

  // ---------- Result screen ----------
  if (result) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-institutional-50 via-white to-heritage-50 py-10 px-4">
        <div className="max-w-3xl mx-auto">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
            <div className="text-center mb-8">
              <div className="w-16 h-16 mx-auto bg-green-100 rounded-full flex items-center justify-center mb-4">
                <CheckCircle2 className="w-8 h-8 text-green-600" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                ¡Evaluación completada!
              </h1>
              <div
                className={cn(
                  'inline-flex items-center gap-2 px-4 py-2 rounded-full border text-sm font-semibold',
                  LEVEL_COLOR[result.level]
                )}
              >
                <TrendingUp className="w-4 h-4" />
                Tu nivel: {LEVEL_LABEL[result.level]}
              </div>
              <p className="text-sm text-gray-500 mt-3">
                Puntaje: {result.score.toFixed(1)} / 100 · Confianza:{' '}
                {Math.round(result.confidence * 100)}%
              </p>
            </div>

            <p className="text-gray-700 leading-relaxed mb-6">{result.feedback}</p>

            <h3 className="text-sm font-semibold text-gray-900 mb-3 uppercase tracking-wide">
              Desempeño por módulo
            </h3>
            <div className="space-y-3 mb-8">
              {result.module_breakdown.map((m) => (
                <div key={m.module_id}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-700">{m.module_title}</span>
                    <span className="text-gray-500">
                      {m.correct}/{m.total} · {m.percentage.toFixed(0)}%
                    </span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 transition-all"
                      style={{ width: `${m.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            <Button onClick={handleGoDashboard} className="w-full">
              Ir al panel de inicio
            </Button>
          </div>
        </div>
      </div>
    )
  }

  // ---------- Submitting / "IA analyzing" screen ----------
  if (submitMutation.isPending) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-institutional-50 via-white to-heritage-50 text-center px-4">
        <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-6 animate-pulse">
          <Sparkles className="w-8 h-8 text-primary-600" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">
          La IA está analizando tu nivel...
        </h2>
        <p className="text-gray-500 text-sm max-w-md">
          Estamos calculando tu perfil de aprendizaje para personalizar quizzes y desafíos.
        </p>
      </div>
    )
  }

  // ---------- Intro / generating screen ----------
  if (!session) {
    const generating = startMutation.isPending
    return (
      <div className="min-h-dvh bg-gradient-to-br from-institutional-50 via-white to-heritage-50 py-10 px-4 flex items-center">
        <div className="max-w-2xl mx-auto w-full">
          <div className="flex justify-center mb-6">
            <BrandLogo variant="stacked" />
          </div>
          <div className="bg-white rounded-2xl shadow-brand-lg border border-gray-200 p-8 animate-fade-in-up">
            <div className="text-center mb-6">
              <span className="heritage-accent-bar mx-auto mb-4" />
              <div
                className={cn(
                  'w-16 h-16 mx-auto bg-institutional-50 rounded-full flex items-center justify-center mb-4',
                  generating && 'animate-pulse'
                )}
              >
                <Sparkles className="w-8 h-8 text-institutional-700" aria-hidden="true" />
              </div>
              <h1 className="text-2xl font-extrabold text-institutional-700 mb-2">
                Evaluación de Entrada
              </h1>
              <p className="text-gray-600 text-sm leading-relaxed">
                Antes de empezar, necesitamos conocer tu nivel. Responderás{' '}
                <strong>~12 preguntas</strong> sobre los 5 módulos del curso. No te
                preocupes si no sabes alguna — esta evaluación ayuda a personalizar tu
                experiencia.
              </p>
            </div>

            {generating ? (
              <div className="text-center py-8">
                <p className="text-gray-700 font-medium mb-2">
                  La IA está generando tus preguntas...
                </p>
                <p className="text-sm text-gray-500">
                  Esto puede tomar unos segundos.
                </p>
                <div className="mt-4 flex gap-1 justify-center">
                  <div
                    className="w-2 h-2 bg-primary-400 rounded-full animate-bounce"
                    style={{ animationDelay: '0ms' }}
                  />
                  <div
                    className="w-2 h-2 bg-primary-400 rounded-full animate-bounce"
                    style={{ animationDelay: '150ms' }}
                  />
                  <div
                    className="w-2 h-2 bg-primary-400 rounded-full animate-bounce"
                    style={{ animationDelay: '300ms' }}
                  />
                </div>
              </div>
            ) : (
              <Button onClick={handleStart} className="w-full" size="lg">
                Comenzar evaluación
              </Button>
            )}

            {startMutation.isError && (
              <div className="mt-4 p-3 rounded-lg bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm flex gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>
                  No pudimos generar la evaluación. Intenta de nuevo en un momento.
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // ---------- Question wizard ----------
  const q = session.questions[currentIdx]
  const total = session.questions.length
  const progress = ((currentIdx + 1) / total) * 100
  const answeredCount = Object.keys(answers).length
  const isLast = currentIdx === total - 1

  return (
    <div className="min-h-screen bg-gradient-to-br from-institutional-50 via-white to-heritage-50 py-10 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Progress */}
        <div className="mb-6">
          <div className="flex justify-between text-xs text-gray-500 mb-2">
            <span>
              Pregunta {currentIdx + 1} de {total}
            </span>
            <span>{answeredCount} respondidas</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-500 transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 sm:p-8">
          <div className="flex gap-2 mb-4 flex-wrap">
            <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600 font-medium">
              Módulo {q.module_id}
            </span>
            <span
              className={cn(
                'text-xs px-2 py-1 rounded font-medium',
                q.difficulty === 'easy' && 'bg-green-100 text-green-700',
                q.difficulty === 'medium' && 'bg-yellow-100 text-yellow-700',
                q.difficulty === 'hard' && 'bg-red-100 text-red-700'
              )}
            >
              {DIFFICULTY_LABEL[q.difficulty] || q.difficulty}
            </span>
          </div>

          <p className="font-medium text-gray-900 text-lg leading-relaxed mb-6">
            {q.question_text}
          </p>

          <div className="space-y-2">
            {q.options.map((opt, i) => (
              <button
                key={i}
                onClick={() => handleSelect(q.id, i)}
                className={cn(
                  'w-full text-left px-4 py-3 rounded-lg border-2 transition text-sm',
                  answers[q.id] === i
                    ? 'border-primary-500 bg-primary-50 text-primary-800'
                    : 'border-gray-200 hover:border-gray-300 text-gray-700'
                )}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>

        {/* Nav buttons */}
        <div className="flex items-center justify-between mt-6">
          <Button
            variant="outline"
            onClick={handlePrev}
            disabled={currentIdx === 0}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Anterior
          </Button>

          {isLast ? (
            <Button onClick={handleSubmit} disabled={submitMutation.isPending}>
              Enviar evaluación
            </Button>
          ) : (
            <Button onClick={handleNext}>
              Siguiente
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          )}
        </div>

        <p className="text-center text-xs text-gray-400 mt-4 flex items-center gap-1 justify-center">
          <Sparkles className="w-3 h-3" />
          Preguntas generadas por IA —{' '}
          {session.source === 'ai' ? 'generadas en vivo' : 'banco de respaldo'}
        </p>
      </div>
    </div>
  )
}
