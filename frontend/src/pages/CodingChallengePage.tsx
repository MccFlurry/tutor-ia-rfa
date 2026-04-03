import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  ChevronRight,
  Play,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  XCircle,
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
import { Button } from '@/components/ui/button'
import { codingApi } from '@/api/coding'
import { topicsApi } from '@/api/topics'
import type { CodingEvaluation } from '@/types/coding'

const difficultyConfig = {
  easy: { label: 'Fácil', color: 'bg-green-100 text-green-700' },
  medium: { label: 'Intermedio', color: 'bg-amber-100 text-amber-700' },
  hard: { label: 'Difícil', color: 'bg-red-100 text-red-700' },
}

export default function CodingChallengePage() {
  const { challengeId } = useParams<{ challengeId: string }>()
  const navigate = useNavigate()
  const cid = Number(challengeId)

  const [code, setCode] = useState('')
  const [showHints, setShowHints] = useState(false)
  const [result, setResult] = useState<CodingEvaluation | null>(null)

  // Fetch challenge
  const { data: challenge, isLoading, isError } = useQuery({
    queryKey: ['coding-challenge', cid],
    queryFn: async () => {
      const { data } = await codingApi.getChallenge(cid)
      return data
    },
    enabled: !!challengeId,
  })

  // Get topic for breadcrumb
  const { data: topic } = useQuery({
    queryKey: ['topic', challenge?.topic_id],
    queryFn: () => topicsApi.get(challenge!.topic_id).then((r) => r.data),
    enabled: !!challenge?.topic_id,
  })

  // Initialize code when challenge loads
  if (challenge && !code && !result) {
    setCode(challenge.initial_code || '')
  }

  // Fetch best submission
  const { data: bestSubmission } = useQuery({
    queryKey: ['coding-best', cid],
    queryFn: async () => {
      const { data } = await codingApi.getBest(cid)
      return data
    },
    enabled: !!challengeId,
  })

  // Submit mutation
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
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || 'Error al evaluar el código.')
    },
  })

  const handleSubmit = () => {
    if (!code.trim()) {
      toast.error('Escribe tu código antes de enviar')
      return
    }
    submitMutation.mutate()
  }

  const handleRetry = () => {
    setResult(null)
    setCode(challenge?.initial_code || '')
  }

  const diff = challenge ? difficultyConfig[challenge.difficulty as keyof typeof difficultyConfig] : null

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6">
        <div className="flex flex-col items-center justify-center py-24">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-6 animate-pulse">
            <Code2 className="w-8 h-8 text-primary-600" />
          </div>
          <p className="text-gray-500">Cargando desafío...</p>
        </div>
      </div>
    )
  }

  if (isError || !challenge) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6">
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <AlertTriangle className="w-12 h-12 text-red-400 mb-4" />
          <h2 className="text-lg font-bold text-gray-900 mb-2">Desafío no encontrado</h2>
          <Button variant="outline" onClick={() => navigate(-1)}>Volver</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-gray-500 mb-6 flex-wrap">
        <Link to="/modules" className="hover:text-primary-600 transition">Módulos</Link>
        {topic && (
          <>
            <ChevronRight className="w-4 h-4 shrink-0" />
            <Link to={`/modules/${topic.module.id}`} className="hover:text-primary-600 transition">
              {topic.module.title}
            </Link>
            <ChevronRight className="w-4 h-4 shrink-0" />
            <Link to={`/topics/${topic.id}`} className="hover:text-primary-600 transition">
              {topic.title}
            </Link>
          </>
        )}
        <ChevronRight className="w-4 h-4 shrink-0" />
        <span className="text-gray-900 font-medium">Desafío de Código</span>
      </nav>

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-2xl font-bold text-gray-900">{challenge.title}</h1>
          {diff && (
            <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${diff.color}`}>
              {diff.label}
            </span>
          )}
        </div>
        {bestSubmission && (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Trophy className="w-4 h-4 text-amber-500" />
            <span>Mejor puntuación: {bestSubmission.score}/100</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left column: Problem description */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Code2 className="w-4 h-4 text-primary-500" />
              Descripción del Problema
            </h2>
            <div className="prose prose-sm prose-gray max-w-none prose-code:text-primary-700 prose-code:bg-primary-50 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:before:content-none prose-code:after:content-none">
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
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <button
                onClick={() => setShowHints(!showHints)}
                className="flex items-center gap-2 text-sm font-medium text-amber-700 w-full"
              >
                <Lightbulb className="w-4 h-4" />
                {showHints ? 'Ocultar pista' : 'Mostrar pista'}
              </button>
              {showHints && (
                <p className="text-sm text-amber-800 mt-2 leading-relaxed">{challenge.hints}</p>
              )}
            </div>
          )}

          {/* Evaluation results */}
          {result && (
            <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-primary-500" />
                  Evaluación de la IA
                </h2>
                <div className={`text-2xl font-bold ${
                  result.score >= 80 ? 'text-green-600' :
                  result.score >= 60 ? 'text-amber-600' : 'text-red-600'
                }`}>
                  {result.score}/100
                </div>
              </div>

              {/* Feedback */}
              <div className="prose prose-sm prose-gray max-w-none prose-code:text-primary-700 prose-code:bg-primary-50 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:before:content-none prose-code:after:content-none">
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

              {/* Strengths */}
              {result.strengths && result.strengths.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-green-700 mb-2 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Puntos fuertes
                  </h3>
                  <ul className="space-y-1">
                    {result.strengths.map((s, i) => (
                      <li key={i} className="text-sm text-green-800 bg-green-50 rounded-lg px-3 py-1.5">
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Improvements */}
              {result.improvements && result.improvements.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-amber-700 mb-2 flex items-center gap-1">
                    <ArrowUp className="w-3.5 h-3.5" /> Áreas de mejora
                  </h3>
                  <ul className="space-y-1">
                    {result.improvements.map((s, i) => (
                      <li key={i} className="text-sm text-amber-800 bg-amber-50 rounded-lg px-3 py-1.5">
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
          <div className="bg-gray-900 rounded-xl overflow-hidden border border-gray-700">
            {/* Editor header */}
            <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
              <span className="text-xs text-gray-400 font-mono">{challenge.language}</span>
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500/80" />
                <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                <div className="w-3 h-3 rounded-full bg-green-500/80" />
              </div>
            </div>
            {/* Textarea editor */}
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              disabled={submitMutation.isPending}
              spellCheck={false}
              className="w-full min-h-[400px] bg-gray-900 text-gray-100 font-mono text-sm p-4 resize-y focus:outline-none placeholder:text-gray-600 disabled:opacity-50"
              placeholder="// Escribe tu código aquí..."
            />
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3">
            {result ? (
              <>
                <Button onClick={handleRetry} variant="outline" className="flex-1 gap-2">
                  <RotateCcw className="w-4 h-4" />
                  Intentar de nuevo
                </Button>
                <Button onClick={handleSubmit} disabled={submitMutation.isPending} className="flex-1 gap-2">
                  <Play className="w-4 h-4" />
                  Reenviar código
                </Button>
              </>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={submitMutation.isPending || !code.trim()}
                className="w-full gap-2"
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
    </div>
  )
}
