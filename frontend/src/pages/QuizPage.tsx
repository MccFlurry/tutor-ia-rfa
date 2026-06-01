import { useCallback, useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronRight, Send, Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'
import { quizApi } from '@/api/quiz'
import { topicsApi } from '@/api/topics'
import { Button } from '@/components/ui/button'
import QuizQuestionComponent from '@/components/quiz/QuizQuestion'
import QuizResults from '@/components/quiz/QuizResults'
import TutorNudgeList from '@/components/tutor/TutorNudgeList'
import PageHeader from '@/components/common/PageHeader'
import AILoadingState from '@/components/common/AILoadingState'
import ErrorState from '@/components/common/ErrorState'
import {
  loadQuizState,
  saveQuizState,
  clearQuizState,
} from '@/lib/quizPersistence'
import { handleLevelChange } from '@/lib/levelChange'
import type { QuizGenerateResponse, QuizSubmitResponse } from '@/types/quiz'

export default function QuizPage() {
  const { topicId } = useParams<{ topicId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const tid = Number(topicId)

  // Try to restore prior session for this topic before deciding whether to
  // generate a new quiz. If a fresh persisted session exists, we skip the
  // generation request and rehydrate the user's in-progress answers.
  const [persistedQuiz, setPersistedQuiz] = useState<QuizGenerateResponse | null>(
    () => {
      const saved = loadQuizState(tid)
      return saved ? { session_id: saved.session_id, questions: saved.questions } : null
    }
  )
  const [answers, setAnswers] = useState<Record<string, number>>(
    () => loadQuizState(tid)?.answers ?? {}
  )
  const [result, setResult] = useState<QuizSubmitResponse | null>(null)
  const [generationKey, setGenerationKey] = useState(0)
  const [revealUnanswered, setRevealUnanswered] = useState(false)

  const { data: topic } = useQuery({
    queryKey: ['topic', tid],
    queryFn: () => topicsApi.get(tid).then((r) => r.data),
    enabled: !!topicId,
  })

  // Only generate when we don't already have a persisted/active quiz.
  const {
    data: generated,
    isLoading: isGenerating,
    isError,
    error,
  } = useQuery({
    queryKey: ['quiz', tid, generationKey],
    queryFn: () => quizApi.generate(tid).then((r) => r.data),
    enabled: !!topicId && persistedQuiz === null,
    retry: false,
    staleTime: 25 * 60 * 1000,
  })

  // Hoist freshly generated quiz into local + persistent state.
  useEffect(() => {
    if (generated && !persistedQuiz) {
      setPersistedQuiz(generated)
      saveQuizState(tid, {
        session_id: generated.session_id,
        questions: generated.questions,
        answers: {},
      })
    }
  }, [generated, persistedQuiz, tid])

  const quizData = persistedQuiz ?? generated ?? null
  const sessionId = quizData?.session_id ?? null
  const questions = quizData?.questions ?? []

  // Persist answers as the student progresses.
  useEffect(() => {
    if (!persistedQuiz || result) return
    saveQuizState(tid, {
      session_id: persistedQuiz.session_id,
      questions: persistedQuiz.questions,
      answers,
    })
  }, [answers, persistedQuiz, tid, result])

  const handleRetry = useCallback(() => {
    clearQuizState(tid)
    setAnswers({})
    setResult(null)
    setPersistedQuiz(null)
    setRevealUnanswered(false)
    setGenerationKey((k) => k + 1)
  }, [tid])

  const submitMutation = useMutation({
    mutationFn: () => {
      if (!sessionId) throw new Error('No session')
      return quizApi.submit(tid, sessionId, answers).then((r) => r.data)
    },
    onSuccess: (data) => {
      setResult(data)
      clearQuizState(tid)
      queryClient.removeQueries({ queryKey: ['quiz', tid] })
      if (data.is_passed) {
        toast.success('¡Aprobaste la autoevaluación!')
      }
      handleLevelChange(data.level_change, queryClient)
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
      setRevealUnanswered(true)
      toast.error(`Tienes ${unanswered.length} pregunta(s) sin responder`)
      const first = document.getElementById(`quiz-q-${unanswered[0].id}`)
      if (first) {
        first.scrollIntoView({ behavior: 'smooth', block: 'center' })
        first.focus({ preventScroll: true })
      }
      return
    }
    submitMutation.mutate()
  }

  const errorStatus = (error as any)?.response?.status
  const isServiceUnavailable = errorStatus === 503
  const isLocked = errorStatus === 403

  if (isGenerating && !quizData) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 sm:px-6">
        <AILoadingState
          title="La IA está preparando tus preguntas..."
          subtitle="El tutor inteligente está generando preguntas personalizadas basadas en el contenido del tema. Esto puede tomar unos segundos."
        />
      </div>
    )
  }

  if (isError && !quizData) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 sm:px-6">
        <ErrorState
          variant={isServiceUnavailable ? 'serviceUnavailable' : isLocked ? 'notFound' : 'generic'}
          title={
            isServiceUnavailable
              ? 'Servicio no disponible'
              : isLocked
                ? 'Tema bloqueado'
                : 'Error al generar preguntas'
          }
          description={
            isServiceUnavailable
              ? 'El servicio de generación de preguntas no está disponible en este momento.'
              : isLocked
                ? 'Este tema pertenece a un módulo que aún no has desbloqueado. Completa el módulo anterior para acceder.'
                : 'Ocurrió un error al generar las preguntas. Intenta de nuevo.'
          }
          action={
            isLocked ? (
              <Button variant="outline" onClick={() => navigate('/modules')}>
                Volver a módulos
              </Button>
            ) : (
              <>
                <Button variant="outline" onClick={() => navigate(`/topics/${tid}`)}>
                  Volver al tema
                </Button>
                <Button onClick={handleRetry}>Reintentar</Button>
              </>
            )
          }
        />
      </div>
    )
  }

  const answeredCount = Object.keys(answers).length
  const totalQuestions = questions.length

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 sm:px-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-6 flex-wrap" aria-label="Migas de pan">
        <Link to="/modules" className="hover:text-primary-600 dark:hover:text-primary-400 transition">
          Módulos
        </Link>
        {topic && (
          <>
            <ChevronRight className="w-4 h-4 shrink-0" aria-hidden="true" />
            <Link
              to={`/modules/${topic.module.id}`}
              className="hover:text-primary-600 dark:hover:text-primary-400 transition"
            >
              {topic.module.title}
            </Link>
            <ChevronRight className="w-4 h-4 shrink-0" aria-hidden="true" />
            <Link to={`/topics/${tid}`} className="hover:text-primary-600 dark:hover:text-primary-400 transition">
              {topic.title}
            </Link>
          </>
        )}
        <ChevronRight className="w-4 h-4 shrink-0" aria-hidden="true" />
        <span className="text-foreground font-medium">Autoevaluación</span>
      </nav>

      <PageHeader
        title="Autoevaluación"
        subtitle={
          <>
            {topic?.title} — Responde todas las preguntas y obtén al menos 60% para aprobar.
            <span className="block text-xs mt-1 flex items-center gap-1">
              <Sparkles className="w-3 h-3 inline" aria-hidden="true" />
              Preguntas generadas por IA — tu progreso se guarda automáticamente
            </span>
          </>
        }
      />

      {result ? (
        <div className="space-y-6">
          <TutorNudgeList context="quiz_result" topicId={tid} score={result.score} />
          <QuizResults
            result={result}
            onRetry={handleRetry}
            onBack={() => navigate(`/topics/${tid}`)}
          />
        </div>
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
                invalid={revealUnanswered && answers[q.id] === undefined}
              />
            ))}
          </div>

          {/* Spacer so content doesn't get hidden under sticky bar on mobile */}
          <div aria-hidden="true" className="h-4" />

          {/* Submit bar */}
          <div className="sticky bottom-0 bg-background/95 backdrop-blur border-t border-border -mx-4 px-4 py-3 mt-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between sm:-mx-6 sm:px-6 sm:py-4">
            <span className="text-sm text-muted-foreground tabular-nums text-center sm:text-left">
              {answeredCount} de {totalQuestions} respondidas
            </span>
            <Button
              onClick={handleSubmit}
              disabled={submitMutation.isPending}
              className="w-full sm:w-auto min-h-[44px]"
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
