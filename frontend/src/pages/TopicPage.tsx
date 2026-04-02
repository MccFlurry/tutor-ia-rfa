import { useEffect, useRef } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronRight, ChevronLeft, ArrowRight, CheckCircle2, FileQuestion } from 'lucide-react'
import toast from 'react-hot-toast'
import { topicsApi } from '@/api/topics'
import { modulesApi } from '@/api/modules'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
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
      <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6 space-y-4">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-8 w-96" />
        <Skeleton className="h-[600px] w-full rounded-xl" />
      </div>
    )
  }

  if (!topic) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <p className="text-gray-500">Tema no encontrado.</p>
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
    <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-gray-500 mb-6 flex-wrap">
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
        <span className="text-gray-900 font-medium">{topic.title}</span>
      </nav>

      {/* Topic header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{topic.title}</h1>
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span>{topic.estimated_minutes} min de lectura</span>
          {topic.has_quiz && (
            <span className="flex items-center gap-1">
              <FileQuestion className="w-4 h-4" />
              Tiene autoevaluación
            </span>
          )}
          {isCompleted && (
            <span className="flex items-center gap-1 text-green-600">
              <CheckCircle2 className="w-4 h-4" />
              Completado
            </span>
          )}
        </div>
      </div>

      {/* Video embed */}
      {topic.video_url && (
        <div className="mb-8 aspect-video rounded-xl overflow-hidden bg-gray-900">
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
      <div className="bg-white rounded-xl border border-gray-200 p-6 sm:p-8 mb-8">
        <ContentRenderer content={topic.content_markdown} />
      </div>

      {/* Action buttons */}
      <div className="flex flex-col sm:flex-row gap-3 mb-8">
        {!isCompleted && !topic.has_quiz && (
          <Button
            onClick={() => completeMutation.mutate()}
            disabled={completeMutation.isPending}
            className="bg-green-600 hover:bg-green-700"
          >
            <CheckCircle2 className="w-4 h-4 mr-2" />
            {completeMutation.isPending ? 'Marcando...' : 'Marcar como completado'}
          </Button>
        )}
        {topic.has_quiz && (
          <Button
            onClick={() => navigate(`/quiz/${topic.id}`)}
            variant="outline"
          >
            <FileQuestion className="w-4 h-4 mr-2" />
            Ir a la Autoevaluación
          </Button>
        )}
      </div>

      {/* Prev / Next navigation */}
      <div className="flex items-center justify-between border-t border-gray-200 pt-6">
        {prevTopic ? (
          <Button
            variant="ghost"
            onClick={() => navigate(`/topics/${prevTopic.id}`)}
            className="text-gray-600"
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            {prevTopic.title}
          </Button>
        ) : (
          <div />
        )}

        <span className="text-xs text-gray-400 hidden sm:block">
          {currentIdx + 1} de {siblings.length}
        </span>

        {nextTopic ? (
          <Button
            variant="ghost"
            onClick={() => navigate(`/topics/${nextTopic.id}`)}
            className="text-gray-600"
          >
            {nextTopic.title}
            <ArrowRight className="w-4 h-4 ml-1" />
          </Button>
        ) : (
          <div />
        )}
      </div>
    </div>
  )
}
