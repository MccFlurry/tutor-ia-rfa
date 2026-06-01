import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Sparkles, ChevronLeft, ChevronRight, CheckCircle2, AlertTriangle, TrendingUp, BookOpen } from 'lucide-react'
import toast from 'react-hot-toast'
import { assessmentApi } from '@/api/assessment'
import { usersApi } from '@/api/users'
import { Button } from '@/components/ui/button'
import { RadioGroup } from '@/components/ui/radio-group'
import OptionRadio from '@/components/common/OptionRadio'
import AILoadingState from '@/components/common/AILoadingState'
import { cn } from '@/lib/utils'
import BrandLogo from '@/components/brand/BrandLogo'
import TutorNudgeList from '@/components/tutor/TutorNudgeList'
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
  beginner:     'bg-muted text-foreground border-border',
  intermediate: 'bg-primary-50 text-primary-800 border-primary-200 dark:bg-primary/15 dark:text-primary-200 dark:border-primary-700',
  advanced:     'bg-success/10 text-success border-success/30',
}

const DIFFICULTY_LABEL: Record<string, string> = {
  easy: 'Fácil',
  medium: 'Media',
  hard: 'Difícil',
}

const DIFFICULTY_CHIP: Record<string, string> = {
  easy:   'bg-success/15 text-success',
  medium: 'bg-warning/15 text-warning-foreground dark:text-warning',
  hard:   'bg-destructive/15 text-destructive',
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

  useEffect(() => {
    if (isAdmin) navigate('/admin', { replace: true })
  }, [isAdmin, navigate])

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
      <div className="min-h-dvh flex items-center justify-center bg-gradient-to-br from-institutional-50 via-background to-heritage-50">
        <div className="text-muted-foreground">Cargando...</div>
      </div>
    )
  }

  // ---------- Result screen ----------
  if (result) {
    return (
      <div className="min-h-dvh bg-gradient-to-br from-institutional-50 via-background to-heritage-50 py-10 px-4">
        <div className="max-w-3xl mx-auto">
          <div className="bg-card rounded-2xl shadow-brand-sm border border-border p-5 sm:p-8">
            <div className="text-center mb-8">
              <div
                className="w-16 h-16 mx-auto bg-success/15 rounded-full flex items-center justify-center mb-4"
                aria-hidden="true"
              >
                <CheckCircle2 className="w-8 h-8 text-success" />
              </div>
              <h1 className="text-2xl font-bold text-foreground mb-2">
                ¡Evaluación completada!
              </h1>
              <div
                className={cn(
                  'inline-flex items-center gap-2 px-4 py-2 rounded-full border text-sm font-semibold',
                  LEVEL_COLOR[result.level]
                )}
              >
                <TrendingUp className="w-4 h-4" aria-hidden="true" />
                Tu nivel: {LEVEL_LABEL[result.level]}
              </div>
              <p className="text-sm text-muted-foreground mt-3 tabular-nums">
                Puntaje: {result.score.toFixed(1)} / 100
              </p>
            </div>

            <TutorNudgeList context="assessment_result" score={result.score} />

            <p className="text-foreground leading-relaxed mb-6">{result.feedback}</p>

            <h2 className="text-sm font-semibold text-muted-foreground mb-3">
              Desempeño por módulo
            </h2>
            <div className="space-y-3 mb-8">
              {result.module_breakdown.map((m) => (
                <div key={m.module_id}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-foreground">{m.module_title}</span>
                    <span className="text-muted-foreground tabular-nums">
                      {m.correct}/{m.total} · {m.percentage.toFixed(0)}%
                    </span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden" aria-hidden="true">
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
      <div className="min-h-dvh flex items-center justify-center bg-gradient-to-br from-institutional-50 via-background to-heritage-50 px-4">
        <AILoadingState
          title="La IA está analizando tu nivel..."
          subtitle="Estamos calculando tu perfil de aprendizaje para personalizar quizzes y desafíos."
        />
      </div>
    )
  }

  // ---------- Intro / generating screen ----------
  if (!session) {
    const generating = startMutation.isPending
    return (
      <div className="min-h-dvh bg-gradient-to-br from-institutional-50 via-background to-heritage-50 py-10 px-4 flex items-center">
        <div className="max-w-2xl mx-auto w-full">
          <div className="flex justify-center mb-6">
            <BrandLogo variant="stacked" size={64} />
          </div>
          <div className="bg-card rounded-2xl shadow-brand-lg border border-border p-5 sm:p-8 animate-fade-in-up">
            <div className="text-center mb-6">
              <span className="heritage-accent-bar mx-auto mb-4" />
              <div
                className={cn(
                  'w-16 h-16 mx-auto bg-institutional-50 dark:bg-institutional-700/30 rounded-full flex items-center justify-center mb-4',
                  generating && 'animate-pulse'
                )}
                aria-hidden="true"
              >
                <Sparkles className="w-8 h-8 text-institutional-700 dark:text-institutional-100" />
              </div>
              <h1 className="text-2xl font-extrabold text-institutional-700 dark:text-institutional-100 mb-2">
                Evaluación de Entrada
              </h1>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Antes de empezar, necesitamos conocer tu nivel. Responderás{' '}
                <strong>~12 preguntas</strong> sobre los 5 módulos del curso. No te
                preocupes si no sabes alguna — esta evaluación ayuda a personalizar tu
                experiencia.
              </p>
            </div>

            {generating ? (
              <AILoadingState
                title="La IA está generando tus preguntas..."
                subtitle="Esto puede tomar unos segundos."
              />
            ) : (
              <Button onClick={handleStart} className="w-full" size="lg">
                Comenzar evaluación
              </Button>
            )}

            {startMutation.isError && (
              <div
                role="alert"
                className="mt-4 p-3 rounded-lg bg-warning/10 border border-warning/30 text-warning-foreground dark:text-warning text-sm flex gap-2"
              >
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
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
  const progressPct = ((currentIdx + 1) / total) * 100
  const answeredCount = Object.keys(answers).length
  const isLast = currentIdx === total - 1
  const groupLabelId = `assessment-q-${q.id}-label`

  return (
    <div className="min-h-dvh bg-gradient-to-br from-institutional-50 via-background to-heritage-50 py-10 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Progress */}
        <div className="mb-6">
          <div className="flex justify-between text-xs text-muted-foreground mb-2 tabular-nums">
            <span>
              Pregunta {currentIdx + 1} de {total}
            </span>
            <span>{answeredCount} respondidas</span>
          </div>
          <div
            className="h-2 bg-muted rounded-full overflow-hidden"
            role="progressbar"
            aria-label="Progreso de la evaluación"
            aria-valuenow={currentIdx + 1}
            aria-valuemin={1}
            aria-valuemax={total}
            aria-valuetext={`Pregunta ${currentIdx + 1} de ${total}`}
          >
            <div
              className="h-full bg-primary-500 transition-all"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>

        {session.source === 'bank' && (
          <div className="mb-4 flex items-center gap-1.5 px-3 py-2 rounded-lg bg-muted/60 border border-border text-xs text-muted-foreground w-fit">
            <BookOpen className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
            <span>Banco de preguntas del docente</span>
          </div>
        )}

        <div className="bg-card rounded-2xl shadow-brand-sm border border-border p-5 sm:p-8">
          <div className="flex gap-2 mb-4 flex-wrap">
            <span className="text-xs px-2 py-1 rounded bg-muted text-foreground font-medium">
              Módulo {q.module_id}
            </span>
            <span
              className={cn(
                'text-xs px-2 py-1 rounded font-medium',
                DIFFICULTY_CHIP[q.difficulty] ?? 'bg-muted text-foreground'
              )}
            >
              {DIFFICULTY_LABEL[q.difficulty] || q.difficulty}
            </span>
          </div>

          <p
            id={groupLabelId}
            className="font-medium text-foreground text-base sm:text-lg leading-relaxed mb-6"
          >
            {q.question_text}
          </p>

          <RadioGroup
            value={answers[q.id] !== undefined ? String(answers[q.id]) : undefined}
            onValueChange={(val) => handleSelect(q.id, Number(val))}
            aria-labelledby={groupLabelId}
          >
            {q.options.map((opt, i) => (
              <OptionRadio key={i} value={String(i)}>
                {opt}
              </OptionRadio>
            ))}
          </RadioGroup>
        </div>

        {/* Nav buttons */}
        <div className="flex items-center justify-between gap-3 mt-6">
          <Button
            variant="outline"
            size="lg"
            onClick={handlePrev}
            disabled={currentIdx === 0}
            className="min-h-[44px]"
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Anterior
          </Button>

          {isLast ? (
            <Button
              size="lg"
              onClick={handleSubmit}
              disabled={submitMutation.isPending}
              className="min-h-[44px]"
            >
              Enviar evaluación
            </Button>
          ) : (
            <Button size="lg" onClick={handleNext} className="min-h-[44px]">
              Siguiente
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          )}
        </div>

        {session.source === 'ai' && (
          <p className="text-center text-xs text-muted-foreground mt-4 flex items-center gap-1 justify-center">
            <Sparkles className="w-3 h-3" aria-hidden="true" />
            Preguntas generadas por IA en vivo
          </p>
        )}
      </div>
    </div>
  )
}
