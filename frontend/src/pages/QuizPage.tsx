import { useState, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronRight, Send, Sparkles, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'
import { quizApi } from '@/api/quiz'
import { topicsApi } from '@/api/topics'
import { Button } from '@/components/ui/button'
import QuizQuestionComponent from '@/components/quiz/QuizQuestion'
import QuizResults from '@/components/quiz/QuizResults'
import type { QuizSubmitResponse } from '@/types/quiz'

export default function QuizPage() {
  const { topicId } = useParams<{ topicId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const tid = Number(topicId)

  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [result, setResult] = useState<QuizSubmitResponse | null>(null)
  const [generationKey, setGenerationKey] = useState(0) // increment to force re-fetch

  // Get topic info for breadcrumb
  const { data: topic } = useQuery({
    queryKey: ['topic', tid],
    queryFn: () => topicsApi.get(tid).then((r) => r.data),
    enabled: !!topicId,
  })

  // Generate quiz (AI-powered)
  const {
    data: quizData,
    isLoading: isGenerating,
    isError,
    error,
  } = useQuery({
    queryKey: ['quiz', tid, generationKey],
    queryFn: () => quizApi.generate(tid).then((r) => r.data),
    enabled: !!topicId,
    retry: false,
    staleTime: 0, // Always re-fetch on mount
  })

  const sessionId = quizData?.session_id ?? null
  const questions = quizData?.questions ?? []

  // Submit mutation
  const submitMutation = useMutation({
    mutationFn: () => {
      if (!sessionId) throw new Error('No session')
      return quizApi.submit(tid, sessionId, answers).then((r) => r.data)
    },
    onSuccess: (data) => {
      setResult(data)
      if (data.is_passed) {
        toast.success('¡Aprobaste la autoevaluación!')
      }
      queryClient.invalidateQueries({ queryKey: ['topic', tid] })
      queryClient.invalidateQueries({ queryKey: ['module'] })
      queryClient.invalidateQueries({ queryKey: ['modules'] })
      queryClient.invalidateQueries({ queryKey: ['progress'] })
      queryClient.invalidateQueries({ queryKey: ['achievements'] })
    },
    onError: (err: any) => {
      const status = err?.response?.status
      if (status === 410) {
        toast.error('Tu sesión expiró. Generando nuevas preguntas...')
        handleRetry()
      } else {
        toast.error('Error al enviar las respuestas')
      }
    },
  })

  const handleSelect = (questionId: string, optionIndex: number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }))
  }

  const handleSubmit = () => {
    if (!questions.length) return
    const unanswered = questions.filter((q) => answers[q.id] === undefined)
    if (unanswered.length > 0) {
      toast.error(`Tienes ${unanswered.length} pregunta(s) sin responder`)
      return
    }
    submitMutation.mutate()
  }

  const handleRetry = useCallback(() => {
    setAnswers({})
    setResult(null)
    setGenerationKey((k) => k + 1) // Force new generation
  }, [])

  // Error state
  const errorStatus = (error as any)?.response?.status
  const isServiceUnavailable = errorStatus === 503

  // Generating state (AI loading)
  if (isGenerating) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 sm:px-6">
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-6 animate-pulse">
            <Sparkles className="w-8 h-8 text-primary-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            La IA está preparando tus preguntas...
          </h2>
          <p className="text-gray-500 text-sm max-w-md">
            El tutor inteligente está generando preguntas personalizadas basadas en el
            contenido del tema. Esto puede tomar unos segundos.
          </p>
          <div className="mt-6 flex gap-1">
            <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (isError) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 sm:px-6">
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-6">
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            {isServiceUnavailable
              ? 'Servicio no disponible'
              : 'Error al generar preguntas'}
          </h2>
          <p className="text-gray-500 text-sm max-w-md mb-6">
            {isServiceUnavailable
              ? 'El servicio de generación de preguntas no está disponible en este momento.'
              : 'Ocurrió un error al generar las preguntas. Intenta de nuevo.'}
          </p>
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => navigate(`/topics/${tid}`)}>
              Volver al tema
            </Button>
            <Button onClick={handleRetry}>
              Reintentar
            </Button>
          </div>
        </div>
      </div>
    )
  }

  const answeredCount = Object.keys(answers).length
  const totalQuestions = questions.length

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 sm:px-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-gray-500 mb-6 flex-wrap">
        <Link to="/modules" className="hover:text-primary-600 transition">
          Módulos
        </Link>
        {topic && (
          <>
            <ChevronRight className="w-4 h-4 shrink-0" />
            <Link
              to={`/modules/${topic.module.id}`}
              className="hover:text-primary-600 transition"
            >
              {topic.module.title}
            </Link>
            <ChevronRight className="w-4 h-4 shrink-0" />
            <Link
              to={`/topics/${tid}`}
              className="hover:text-primary-600 transition"
            >
              {topic.title}
            </Link>
          </>
        )}
        <ChevronRight className="w-4 h-4 shrink-0" />
        <span className="text-gray-900 font-medium">Autoevaluación</span>
      </nav>

      <div className="mb-8">
        <span className="heritage-accent-bar mb-3" aria-hidden="true" />
        <h1 className="text-2xl sm:text-3xl font-extrabold text-institutional-700 mb-2">Autoevaluación</h1>
        <p className="text-gray-500 text-sm">
          {topic?.title} — Responde todas las preguntas y obtén al menos 60% para aprobar.
        </p>
        <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
          <Sparkles className="w-3 h-3" />
          Preguntas generadas por IA — cada intento es único
        </p>
      </div>

      {/* Show results or questions */}
      {result ? (
        <QuizResults
          result={result}
          onRetry={handleRetry}
          onBack={() => navigate(`/topics/${tid}`)}
        />
      ) : (
        <>
          <div className="space-y-4">
            {questions.map((q, i) => (
              <QuizQuestionComponent
                key={q.id}
                question={q}
                index={i}
                total={totalQuestions}
                selectedIndex={answers[q.id] ?? null}
                onSelect={(optIdx) => handleSelect(q.id, optIdx)}
                disabled={submitMutation.isPending}
              />
            ))}
          </div>

          {/* Submit bar */}
          <div className="sticky bottom-0 bg-gray-50/95 backdrop-blur border-t border-gray-200 -mx-4 px-4 py-4 mt-6 flex items-center justify-between sm:-mx-6 sm:px-6">
            <span className="text-sm text-gray-500">
              {answeredCount} de {totalQuestions} respondidas
            </span>
            <Button
              onClick={handleSubmit}
              disabled={submitMutation.isPending}
            >
              <Send className="w-4 h-4 mr-2" />
              {submitMutation.isPending ? 'Enviando...' : 'Enviar respuestas'}
            </Button>
          </div>
        </>
      )}
    </div>
  )
}
