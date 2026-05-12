import { useEffect, useRef } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronRight, ChevronLeft, ArrowRight, CheckCircle2, FileQuestion, Code2, Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'
import { topicsApi } from '@/api/topics'
import { codingApi } from '@/api/coding'
import { modulesApi } from '@/api/modules'
import { Button } from '@/components/ui/button'
import Skeleton, { SkeletonLine } from '@/components/common/Skeleton'
import ContentRenderer from '@/components/topics/ContentRenderer'

export default function TopicPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const timeRef = useRef(0)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const topicId = Number(id)

  const { data: topic, isLoading } = useQuery({
    queryKey: ['topic', topicId],
    queryFn: () => topicsApi.get(topicId).then((r) => r.data),
    enabled: !!id,
  })

  // On-demand AI challenge fetch for this topic (only when user clicks button)
  const startCodingMutation = useMutation({
    mutationFn: () => codingApi.getForTopic(topicId).then((r) => r.data),
    onSuccess: (data) => {
      if (data.source === 'fallback') {
        toast('Usando desafío del banco (IA no disponible)', { icon: '⚠️' })
      }
      navigate(`/coding/${data.challenge.id}`)
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || 'No se pudo preparar el desafío')
    },
  })

  // Get sibling topics for prev/next navigation
  const { data: moduleDetail } = useQuery({
    queryKey: ['module', topic?.module.id],
    queryFn: () => modulesApi.get(topic!.module.id).then((r) => r.data),
    enabled: !!topic?.module.id,
  })

  // Register visit on load
  const visitMutation = useMutation({
    mutationFn: () => topicsApi.visit(topicId),
  })

  useEffect(() => {
    if (topicId) {
      visitMutation.mutate()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topicId])

  // Track time spent
  useEffect(() => {
    timeRef.current = 0
    intervalRef.current = setInterval(() => {
      timeRef.current += 30
    }, 30000)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
      if (timeRef.current > 0 && topicId) {
        topicsApi.trackTime(topicId, timeRef.current).catch(() => {})
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topicId])

  // Complete topic mutation
  const completeMutation = useMutation({
    mutationFn: () => topicsApi.complete(topicId),
    onSuccess: () => {
      toast.success('Tema marcado como completado')
      queryClient.invalidateQueries({ queryKey: ['topic', topicId] })
      queryClient.invalidateQueries({ queryKey: ['module'] })
      queryClient.invalidateQueries({ queryKey: ['modules'] })
    },
  })

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-4 p-4 sm:p-6">
        <SkeletonLine width="40%" />
        <SkeletonLine width="80%" />
        <Skeleton variant="rect" className="h-48 w-full" />
        <SkeletonLine />
        <SkeletonLine />
        <SkeletonLine width="90%" />
      </div>
    )
  }

  if (!topic) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <p className="text-muted-foreground">Tema no encontrado.</p>
      </div>
    )
  }

  // Find prev/next topics
  const siblings = moduleDetail?.topics || []
  const currentIdx = siblings.findIndex((t) => t.id === topicId)
  const prevTopic = currentIdx > 0 ? siblings[currentIdx - 1] : null
  const nextTopic = currentIdx < siblings.length - 1 ? siblings[currentIdx + 1] : null

  const isCompleted = topic.progress_info?.is_completed ?? false

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 pb-24 sm:pb-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-6 flex-wrap">
        <Link to="/modules" className="hover:text-primary-600 transition">
          Módulos
        </Link>
        <ChevronRight className="w-4 h-4 shrink-0" />
        <Link
          to={`/modules/${topic.module.id}`}
          className="hover:text-primary-600 transition"
        >
          {topic.module.title}
        </Link>
        <ChevronRight className="w-4 h-4 shrink-0" />
        <span className="text-foreground font-medium">{topic.title}</span>
      </nav>

      {/* Topic header */}
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-institutional-700 mb-2 break-words">{topic.title}</h1>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
          <span>{topic.estimated_minutes} min de lectura</span>
          {topic.has_quiz && (
            <span className="flex items-center gap-1">
              <FileQuestion className="w-4 h-4" />
              Tiene autoevaluación
            </span>
          )}
          {isCompleted && (
            <span className="flex items-center gap-1 text-success">
              <CheckCircle2 className="w-4 h-4" />
              Completado
            </span>
          )}
        </div>
      </div>

      {/* Video embed */}
      {topic.video_url && (
        <div className="mb-8 aspect-video rounded-xl overflow-hidden bg-foreground/90">
          <iframe
            src={topic.video_url}
            title={topic.title}
            className="w-full h-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      )}

      {/* Content */}
      <div className="bg-card rounded-xl border border-border p-4 sm:p-8 mb-8">
        <ContentRenderer content={topic.content_markdown} />
      </div>

      {/* Action buttons */}
      <div className="flex flex-col sm:flex-row gap-3 mb-8">
        {!isCompleted && !topic.has_quiz && (
          <Button
            onClick={() => completeMutation.mutate()}
            disabled={completeMutation.isPending}
            className="bg-success hover:bg-success/90 text-success-foreground w-full sm:w-auto min-h-[44px]"
          >
            <CheckCircle2 className="w-4 h-4 mr-2" />
            {completeMutation.isPending ? 'Marcando...' : 'Marcar como completado'}
          </Button>
        )}
        {topic.has_quiz && (
          <Button
            onClick={() => navigate(`/quiz/${topic.id}`)}
            variant="outline"
            className="w-full sm:w-auto min-h-[44px]"
          >
            <FileQuestion className="w-4 h-4 mr-2" />
            Ir a la Autoevaluación
          </Button>
        )}
        {topic.has_coding_challenge && (
          <Button
            onClick={() => startCodingMutation.mutate()}
            disabled={startCodingMutation.isPending}
            variant="outline"
            className="border-heritage-300 text-heritage-700 hover:bg-heritage-50 w-full sm:w-auto min-h-[44px]"
          >
            {startCodingMutation.isPending ? (
              <>
                <Sparkles className="w-4 h-4 mr-2 animate-pulse" />
                Preparando desafío con IA...
              </>
            ) : (
              <>
                <Code2 className="w-4 h-4 mr-2" />
                Desafío de Código
              </>
            )}
          </Button>
        )}
      </div>

      {/* Prev / Next navigation — sticky on mobile so it stays reachable */}
      <div className="sticky bottom-0 sm:static -mx-4 sm:mx-0 px-4 sm:px-0 py-3 sm:py-0 bg-background/95 sm:bg-transparent backdrop-blur sm:backdrop-blur-0 border-t border-border sm:pt-6 flex items-center justify-between gap-2">
        {prevTopic ? (
          <Button
            variant="ghost"
            onClick={() => navigate(`/topics/${prevTopic.id}`)}
            className="text-muted-foreground min-h-[44px] max-w-[45%] sm:max-w-none"
          >
            <ChevronLeft className="w-4 h-4 mr-1 shrink-0" />
            <span className="truncate">{prevTopic.title}</span>
          </Button>
        ) : (
          <div />
        )}

        <span className="text-xs text-muted-foreground hidden sm:block">
          {currentIdx + 1} de {siblings.length}
        </span>

        {nextTopic ? (
          <Button
            variant="ghost"
            onClick={() => navigate(`/topics/${nextTopic.id}`)}
            className="text-muted-foreground min-h-[44px] max-w-[45%] sm:max-w-none"
          >
            <span className="truncate">{nextTopic.title}</span>
            <ArrowRight className="w-4 h-4 ml-1 shrink-0" />
          </Button>
        ) : (
          <div />
        )}
      </div>
    </div>
  )
}
