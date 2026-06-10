import { useEffect, useRef, useState, lazy, Suspense } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ChevronRight,
  Play,
  Sparkles,
  CheckCircle2,
  Lightbulb,
  Trophy,
  ArrowUp,
  RotateCcw,
  Code2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CodeBlock from '@/components/topics/CodeBlock'

// Lazy-load Monaco editor (~1MB) so it doesn't ship with the initial bundle.
const Editor = lazy(() => import('@monaco-editor/react'))

function EditorFallback() {
  return (
    <div className="h-[320px] lg:h-[480px] bg-foreground/90 dark:bg-card flex items-center justify-center text-sm text-muted-foreground">
      Cargando editor de código...
    </div>
  )
}
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog'
import Skeleton, { SkeletonLine } from '@/components/common/Skeleton'
import ErrorState from '@/components/common/ErrorState'
import { codingApi } from '@/api/coding'
import { topicsApi } from '@/api/topics'
import { useMediaQuery } from '@/hooks/useMediaQuery'
import { useThemeStore } from '@/store/themeStore'
import { handleLevelChange } from '@/lib/levelChange'
import { loadCodeDraft, saveCodeDraft } from '@/lib/codingPersistence'
import TutorNudgeList from '@/components/tutor/TutorNudgeList'
import type { CodingEvaluation } from '@/types/coding'

const difficultyConfig = {
  easy:   { label: 'Fácil',      color: 'bg-success/15 text-success' },
  medium: { label: 'Intermedio', color: 'bg-warning/15 text-warning-foreground dark:text-warning' },
  hard:   { label: 'Difícil',    color: 'bg-foreground/10 text-foreground dark:bg-foreground/15' },
}

export default function CodingChallengePage() {
  const { challengeId } = useParams<{ challengeId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const cid = Number(challengeId)

  const [code, setCode] = useState('')
  const [showHints, setShowHints] = useState(false)
  const [result, setResult] = useState<CodingEvaluation | null>(null)
  const [regenerateDialogOpen, setRegenerateDialogOpen] = useState(false)
  const [resetDialogOpen, setResetDialogOpen] = useState(false)
  const resultRef = useRef<HTMLDivElement>(null)
  const isLgUp = useMediaQuery('(min-width: 1024px)')
  const editorHeight = isLgUp ? '480px' : '320px'
  const isDark = useThemeStore((s) => s.isDark)
  const handleSubmitRef = useRef<() => void>(() => {})

  const { data: challenge, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['coding-challenge', cid],
    queryFn: async () => {
      const { data } = await codingApi.getChallenge(cid)
      return data
    },
    enabled: !!challengeId,
  })

  const { data: topic } = useQuery({
    queryKey: ['topic', challenge?.topic_id],
    queryFn: () => topicsApi.get(challenge!.topic_id).then((r) => r.data),
    enabled: !!challenge?.topic_id,
  })

  useEffect(() => {
    if (challenge) {
      // Rehydrate a saved draft for this challenge; fall back to the starter code.
      setCode(loadCodeDraft(challenge.id) ?? challenge.initial_code ?? '')
      setResult(null)
    }
  }, [challenge?.id])

  const { data: bestSubmission } = useQuery({
    queryKey: ['coding-best', cid],
    queryFn: async () => {
      const { data } = await codingApi.getBest(cid)
      return data
    },
    enabled: !!challengeId,
  })

  const submitMutation = useMutation({
    mutationFn: async () => {
      const { data } = await codingApi.submitCode(cid, code)
      return data
    },
    onSuccess: (data) => {
      setResult(data)
      if (data.score >= 80) {
        toast.success('¡Excelente trabajo!')
      } else if (data.score >= 60) {
        toast.success('¡Buen intento! Revisa las sugerencias.')
      }
      handleLevelChange(data.level_change, queryClient)
      queryClient.invalidateQueries({ queryKey: ['coding-best', cid] })
      queryClient.invalidateQueries({ queryKey: ['tutor-companion'] })
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || 'Error al evaluar el código.')
    },
  })

  const regenerateMutation = useMutation({
    mutationFn: async () => {
      if (!challenge?.topic_id) throw new Error('Tema no disponible')
      const { data } = await codingApi.regenerateForTopic(challenge.topic_id)
      return data
    },
    onSuccess: (data) => {
      setRegenerateDialogOpen(false)
      if (!data?.challenge?.id) {
        toast.error('Respuesta inválida del servidor')
        return
      }
      if (data.source === 'fallback') {
        toast('Se usó desafío del banco (IA no disponible)', { icon: '⚠️' })
      } else {
        toast.success('Nuevo desafío generado')
      }
      navigate(`/coding/${data.challenge.id}`, { replace: true })
    },
    onError: (err: any) => {
      setRegenerateDialogOpen(false)
      toast.error(err?.response?.data?.detail || 'No se pudo regenerar el desafío')
    },
  })

  const handleSubmit = () => {
    if (!code.trim()) {
      toast.error('Escribe tu código antes de enviar')
      return
    }
    submitMutation.mutate()
  }

  useEffect(() => {
    handleSubmitRef.current = handleSubmit
  })

  const handleReset = () => {
    const init = challenge?.initial_code || ''
    setResult(null)
    setCode(init)
    if (challenge) saveCodeDraft(challenge.id, init)
    setResetDialogOpen(false)
  }

  // Bring the AI evaluation into view after submit (on mobile it renders above the editor).
  useEffect(() => {
    if (result && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
      resultRef.current.focus({ preventScroll: true })
    }
  }, [result])

  const diff = challenge ? difficultyConfig[challenge.difficulty as keyof typeof difficultyConfig] : null

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-4 p-4 sm:p-6">
        <div className="space-y-3">
          <SkeletonLine width="40%" />
          <SkeletonLine />
          <SkeletonLine />
          <SkeletonLine width="80%" />
          <Skeleton variant="rect" className="h-24 w-full" />
        </div>
        <Skeleton variant="rect" className="h-[320px] lg:h-[480px] w-full" />
      </div>
    )
  }

  if (isError || !challenge) {
    const status = (error as any)?.response?.status
    const notFound = status === 404
    return (
      <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6">
        <ErrorState
          variant={notFound ? 'notFound' : 'generic'}
          title={notFound ? 'Desafío no encontrado' : 'No pudimos cargar el desafío'}
          description={
            notFound
              ? 'Este desafío no existe o fue movido. Vuelve y selecciona otro.'
              : 'Hubo un problema al cargar el desafío. Revisa tu conexión e inténtalo de nuevo.'
          }
          action={
            <>
              <Button variant="outline" onClick={() => navigate('/modules')}>
                Volver a módulos
              </Button>
              {!notFound && <Button onClick={() => refetch()}>Reintentar</Button>}
            </>
          }
        />
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-6 flex-wrap" aria-label="Migas de pan">
        <Link to="/modules" className="hover:text-primary-600 dark:hover:text-primary-400 transition">Módulos</Link>
        {topic?.module && (
          <>
            <ChevronRight className="w-4 h-4 shrink-0" aria-hidden="true" />
            <Link to={`/modules/${topic.module.id}`} className="hover:text-primary-600 dark:hover:text-primary-400 transition">
              {topic.module.title}
            </Link>
            <ChevronRight className="w-4 h-4 shrink-0" aria-hidden="true" />
            <Link to={`/topics/${topic.id}`} className="hover:text-primary-600 dark:hover:text-primary-400 transition">
              {topic.title}
            </Link>
          </>
        )}
        <ChevronRight className="w-4 h-4 shrink-0" aria-hidden="true" />
        <span className="text-foreground font-medium">Desafío de Código</span>
      </nav>

      {/* Header */}
      <div className="mb-6 flex items-start justify-between flex-wrap gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-3 mb-2 flex-wrap">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-institutional-700 dark:text-institutional-100">{challenge.title}</h1>
            {diff && (
              <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${diff.color}`}>
                {diff.label}
              </span>
            )}
            {challenge.is_ai_generated && (
              <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full bg-heritage-100 text-heritage-700 dark:bg-heritage-700/20 dark:text-heritage-200">
                <Sparkles className="w-3 h-3" aria-hidden="true" />
                Generado con IA
                {challenge.student_level && (
                  <span className="ml-1 text-heritage-600 dark:text-heritage-400">· nivel {challenge.student_level}</span>
                )}
              </span>
            )}
          </div>
          {bestSubmission && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Trophy className="w-4 h-4 text-heritage-600 dark:text-heritage-400" aria-hidden="true" />
              <span className="tabular-nums">Mejor puntuación: {bestSubmission.score}/100</span>
            </div>
          )}
        </div>

        {challenge.is_ai_generated && (
          <Button
            variant="outline"
            onClick={() => setRegenerateDialogOpen(true)}
            disabled={regenerateMutation.isPending}
            className="w-full sm:w-auto min-h-[44px]"
          >
            {regenerateMutation.isPending ? (
              <>
                <Sparkles className="w-4 h-4 mr-1 animate-pulse" />
                Regenerando...
              </>
            ) : (
              <>
                <RotateCcw className="w-4 h-4 mr-1" />
                Regenerar con IA
              </>
            )}
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left column: Problem description */}
        <div className="space-y-4">
          <div className="bg-card rounded-xl border border-border p-5">
            <h2 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
              <Code2 className="w-4 h-4 text-primary-500" aria-hidden="true" />
              Descripción del Problema
            </h2>
            <div className="prose prose-sm prose-gray dark:prose-invert max-w-none prose-code:text-primary-700 dark:prose-code:text-primary-300 prose-code:bg-primary-50 dark:prose-code:bg-primary/15 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:before:content-none prose-code:after:content-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    const codeString = String(children).replace(/\n$/, '')
                    if (match) return <CodeBlock language={match[1]}>{codeString}</CodeBlock>
                    return <code className={className} {...props}>{children}</code>
                  },
                }}
              >
                {challenge.description}
              </ReactMarkdown>
            </div>
          </div>

          {/* Hints */}
          {challenge.hints && (
            <div className="bg-warning/10 border border-warning/30 rounded-xl p-4">
              <button
                onClick={() => setShowHints(!showHints)}
                aria-expanded={showHints}
                className="flex items-center gap-2 text-sm font-medium text-warning-foreground dark:text-warning w-full min-h-[44px]
                           focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
              >
                <Lightbulb className="w-4 h-4" aria-hidden="true" />
                {showHints ? 'Ocultar pista' : 'Mostrar pista'}
              </button>
              {showHints && (
                <p className="text-sm text-foreground mt-2 leading-relaxed">{challenge.hints}</p>
              )}
            </div>
          )}

          {/* Evaluation results */}
          {result && (
            <div
              ref={resultRef}
              tabIndex={-1}
              className="bg-card rounded-xl border border-border p-5 space-y-4 scroll-mt-24 focus:outline-none"
            >
              <TutorNudgeList context="coding_result" score={result.score} />
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-primary-500" aria-hidden="true" />
                  Evaluación de la IA
                </h2>
                <div
                  className={`text-2xl font-bold tabular-nums ${
                    result.score >= 80 ? 'text-success' :
                    result.score >= 60 ? 'text-warning-foreground dark:text-warning' : 'text-destructive'
                  }`}
                >
                  {result.score}/100
                </div>
              </div>

              <div className="prose prose-sm prose-gray dark:prose-invert max-w-none prose-code:text-primary-700 dark:prose-code:text-primary-300 prose-code:bg-primary-50 dark:prose-code:bg-primary/15 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:before:content-none prose-code:after:content-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '')
                      const codeString = String(children).replace(/\n$/, '')
                      if (match) return <CodeBlock language={match[1]}>{codeString}</CodeBlock>
                      return <code className={className} {...props}>{children}</code>
                    },
                  }}
                >
                  {result.feedback}
                </ReactMarkdown>
              </div>

              {result.strengths && result.strengths.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-success mb-2 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" /> Puntos fuertes
                  </h3>
                  <ul className="space-y-1">
                    {result.strengths.map((s, i) => (
                      <li key={i} className="text-sm text-foreground bg-success/10 rounded-lg px-3 py-1.5">
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {result.improvements && result.improvements.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-warning-foreground dark:text-warning mb-2 flex items-center gap-1">
                    <ArrowUp className="w-3.5 h-3.5" aria-hidden="true" /> Áreas de mejora
                  </h3>
                  <ul className="space-y-1">
                    {result.improvements.map((s, i) => (
                      <li key={i} className="text-sm text-foreground bg-warning/10 rounded-lg px-3 py-1.5">
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right column: Code editor */}
        <div className="space-y-4">
          <div className="bg-card rounded-xl overflow-hidden border border-border">
            <div className="flex items-center justify-between px-4 py-2 bg-muted border-b border-border">
              <span className="text-xs text-muted-foreground font-mono">{challenge.language}</span>
              <span className="hidden sm:inline text-[10px] text-muted-foreground/70 font-mono tabular-nums">
                Ctrl+Enter para enviar
              </span>
            </div>
            <Suspense fallback={<EditorFallback />}>
              <Editor
                value={code}
                onChange={(value) => {
                  const v = value ?? ''
                  setCode(v)
                  if (challenge) saveCodeDraft(challenge.id, v)
                }}
                language={challenge.language?.toLowerCase() === 'kotlin' ? 'kotlin' : 'plaintext'}
                theme={isDark ? 'vs-dark' : 'light'}
                height={editorHeight}
                loading={<div className="p-4 text-sm text-muted-foreground">Cargando editor...</div>}
                onMount={(editor, monaco) => {
                  editor.addCommand(
                    monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter,
                    () => handleSubmitRef.current(),
                  )
                }}
                options={{
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: 14,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  wordWrap: 'on',
                  tabSize: 4,
                  insertSpaces: true,
                  automaticLayout: true,
                  readOnly: submitMutation.isPending,
                  renderLineHighlight: 'gutter',
                  smoothScrolling: true,
                  cursorBlinking: 'smooth',
                  padding: { top: 12, bottom: 12 },
                }}
              />
            </Suspense>
          </div>

          {/* Action buttons */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            {result ? (
              <>
                <Button onClick={() => setResetDialogOpen(true)} variant="outline" className="flex-1 gap-2 min-h-[44px]">
                  <RotateCcw className="w-4 h-4" />
                  Reiniciar a la plantilla
                </Button>
                <Button onClick={handleSubmit} disabled={submitMutation.isPending} className="flex-1 gap-2 min-h-[44px]">
                  <Play className="w-4 h-4" />
                  Reenviar código
                </Button>
              </>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={submitMutation.isPending || !code.trim()}
                className="w-full gap-2 min-h-[44px]"
              >
                {submitMutation.isPending ? (
                  <>
                    <Sparkles className="w-4 h-4 animate-spin" />
                    La IA está evaluando tu código...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Enviar código para evaluación
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Regenerate confirmation dialog */}
      <Dialog open={regenerateDialogOpen} onOpenChange={setRegenerateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>¿Generar un desafío nuevo?</DialogTitle>
            <DialogDescription>
              La IA generará un nuevo desafío para este tema. Perderás el código que has escrito.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline" disabled={regenerateMutation.isPending}>
                Cancelar
              </Button>
            </DialogClose>
            <Button
              onClick={() => regenerateMutation.mutate()}
              disabled={regenerateMutation.isPending}
              className="gap-2"
            >
              {regenerateMutation.isPending ? (
                <>
                  <Sparkles className="w-4 h-4 animate-pulse" />
                  Regenerando...
                </>
              ) : (
                <>
                  <RotateCcw className="w-4 h-4" />
                  Regenerar
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reset-to-template confirmation — discarding the student's code is deliberate */}
      <Dialog open={resetDialogOpen} onOpenChange={setResetDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>¿Reiniciar a la plantilla?</DialogTitle>
            <DialogDescription>
              Se descartará el código que escribiste y volverás a la plantilla inicial.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline">Cancelar</Button>
            </DialogClose>
            <Button onClick={handleReset} className="gap-2">
              <RotateCcw className="w-4 h-4" />
              Reiniciar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
