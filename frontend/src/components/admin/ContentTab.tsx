import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ChevronDown, ChevronRight, Plus, Pencil, Trash2, Sparkles, FileText, HelpCircle, Code2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { adminApi, type ModuleAdmin, type TopicAdmin, type GeneratedChallengePreview } from '@/api/admin'
import type { Difficulty, StudentLevel } from '@/types/assessment'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export default function ContentTab() {
  const queryClient = useQueryClient()
  const [expandedModule, setExpandedModule] = useState<number | null>(null)
  const [expandedTopic, setExpandedTopic] = useState<number | null>(null)

  const { data: modules } = useQuery({
    queryKey: ['admin', 'modules'],
    queryFn: () => adminApi.listModules().then((r) => r.data),
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['admin'] })
  }

  // Module mutations
  const createModule = useMutation({
    mutationFn: adminApi.createModule,
    onSuccess: () => { toast.success('Módulo creado'); invalidate() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Error'),
  })
  const updateModule = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => adminApi.updateModule(id, data),
    onSuccess: () => { toast.success('Módulo actualizado'); invalidate() },
  })
  const deleteModule = useMutation({
    mutationFn: adminApi.deleteModule,
    onSuccess: () => { toast.success('Módulo eliminado'); invalidate() },
  })

  const handleCreateModule = () => {
    const title = prompt('Título del módulo:')
    if (!title) return
    const orderStr = prompt('Índice de orden (número):', String((modules?.length || 0) + 1))
    const order_index = Number(orderStr)
    if (!Number.isInteger(order_index) || order_index < 1) return toast.error('Índice inválido')
    createModule.mutate({ title, order_index })
  }

  const handleEditModule = (m: ModuleAdmin) => {
    const title = prompt('Título:', m.title)
    if (title === null) return
    const desc = prompt('Descripción:', m.description || '') || ''
    updateModule.mutate({ id: m.id, data: { title, description: desc } })
  }

  const handleDeleteModule = (m: ModuleAdmin) => {
    if (confirm(`¿Eliminar módulo "${m.title}" y todos sus temas?`)) {
      deleteModule.mutate(m.id)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-gray-900">Árbol del curso</h3>
        <Button size="sm" onClick={handleCreateModule}>
          <Plus className="w-4 h-4 mr-1" /> Módulo nuevo
        </Button>
      </div>

      {!modules || modules.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-8 text-center text-gray-500 text-sm">
          Sin módulos aún.
        </div>
      ) : (
        <div className="space-y-2">
          {modules.map((m) => (
            <div key={m.id} className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 hover:bg-gray-50">
                <button
                  onClick={() => setExpandedModule((prev) => (prev === m.id ? null : m.id))}
                  className="flex items-center gap-2 flex-1 min-w-0 text-left"
                >
                  {expandedModule === m.id ? (
                    <ChevronDown className="w-4 h-4 text-gray-400 shrink-0" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-400 shrink-0" />
                  )}
                  <span
                    className="w-6 h-6 rounded text-xs text-white flex items-center justify-center font-bold shrink-0"
                    style={{ backgroundColor: m.color_hex }}
                  >
                    {m.order_index}
                  </span>
                  <span className="font-medium text-gray-900 truncate">{m.title}</span>
                </button>
                <div className="flex gap-1 shrink-0">
                  <Button size="sm" variant="ghost" onClick={() => handleEditModule(m)}>
                    <Pencil className="w-3 h-3" />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => handleDeleteModule(m)}>
                    <Trash2 className="w-3 h-3 text-red-500" />
                  </Button>
                </div>
              </div>

              {expandedModule === m.id && (
                <ModuleDetail
                  module={m}
                  expandedTopic={expandedTopic}
                  onToggleTopic={(id) => setExpandedTopic((prev) => (prev === id ? null : id))}
                  onRefresh={invalidate}
                />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ---------- Module Detail (topics list + create) ----------

function ModuleDetail({
  module,
  expandedTopic,
  onToggleTopic,
  onRefresh,
}: {
  module: ModuleAdmin
  expandedTopic: number | null
  onToggleTopic: (id: number) => void
  onRefresh: () => void
}) {
  const { data: topics } = useQuery({
    queryKey: ['admin', 'topics', module.id],
    queryFn: () => adminApi.listTopics(module.id).then((r) => r.data),
  })

  const createTopic = useMutation({
    mutationFn: adminApi.createTopic,
    onSuccess: () => { toast.success('Tema creado'); onRefresh() },
    onError: () => toast.error('Error al crear tema'),
  })

  const updateTopic = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => adminApi.updateTopic(id, data),
    onSuccess: () => { toast.success('Tema actualizado'); onRefresh() },
  })

  const deleteTopic = useMutation({
    mutationFn: adminApi.deleteTopic,
    onSuccess: () => { toast.success('Tema eliminado'); onRefresh() },
  })

  const handleCreate = () => {
    const title = prompt('Título del tema:')
    if (!title) return
    const orderStr = prompt('Orden:', String((topics?.length || 0) + 1))
    const order_index = Number(orderStr)
    if (!Number.isInteger(order_index) || order_index < 1) return toast.error('Orden inválido')
    const content = prompt('Contenido inicial (Markdown):', '# ' + title) || ''
    const hasQuizStr = confirm('¿Este tema tiene autoevaluación?')
    createTopic.mutate({
      module_id: module.id,
      title,
      content,
      order_index,
      estimated_minutes: 15,
      has_quiz: hasQuizStr,
    })
  }

  const handleEdit = (t: TopicAdmin) => {
    const title = prompt('Título:', t.title)
    if (title === null) return
    updateTopic.mutate({ id: t.id, data: { title } })
  }

  const handleDelete = (t: TopicAdmin) => {
    if (confirm(`¿Eliminar tema "${t.title}"?`)) deleteTopic.mutate(t.id)
  }

  return (
    <div className="bg-gray-50 px-4 py-3 border-t border-gray-200">
      <div className="flex justify-between items-center mb-3">
        <span className="text-xs font-semibold uppercase text-gray-500">Temas</span>
        <Button size="sm" variant="outline" onClick={handleCreate}>
          <Plus className="w-3 h-3 mr-1" /> Tema
        </Button>
      </div>
      {!topics || topics.length === 0 ? (
        <p className="text-xs text-gray-400 italic">Sin temas</p>
      ) : (
        <div className="space-y-2">
          {topics.map((t) => (
            <div key={t.id} className="bg-white rounded-lg border border-gray-200">
              <div className="flex items-center px-3 py-2 gap-2">
                <button
                  onClick={() => onToggleTopic(t.id)}
                  className="flex items-center gap-2 flex-1 text-left min-w-0"
                >
                  {expandedTopic === t.id ? (
                    <ChevronDown className="w-3 h-3 text-gray-400" />
                  ) : (
                    <ChevronRight className="w-3 h-3 text-gray-400" />
                  )}
                  <FileText className="w-3 h-3 text-gray-400" />
                  <span className="text-sm text-gray-800 truncate">
                    {t.order_index}. {t.title}
                  </span>
                  {t.has_quiz && (
                    <span className="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                      Quiz
                    </span>
                  )}
                </button>
                <Button size="sm" variant="ghost" onClick={() => handleEdit(t)}>
                  <Pencil className="w-3 h-3" />
                </Button>
                <Button size="sm" variant="ghost" onClick={() => handleDelete(t)}>
                  <Trash2 className="w-3 h-3 text-red-500" />
                </Button>
              </div>
              {expandedTopic === t.id && <TopicDetail topic={t} onRefresh={onRefresh} />}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ---------- Topic Detail (quiz + coding lists) ----------

function TopicDetail({ topic, onRefresh }: { topic: TopicAdmin; onRefresh: () => void }) {
  const [genPreview, setGenPreview] = useState<GeneratedChallengePreview | null>(null)

  const { data: questions } = useQuery({
    queryKey: ['admin', 'quiz-questions', topic.id],
    queryFn: () => adminApi.listQuizQuestions(topic.id).then((r) => r.data),
  })

  const { data: challenges } = useQuery({
    queryKey: ['admin', 'coding-challenges', topic.id],
    queryFn: () => adminApi.listChallenges(topic.id).then((r) => r.data),
  })

  const createQ = useMutation({
    mutationFn: adminApi.createQuizQuestion,
    onSuccess: () => { toast.success('Pregunta creada'); onRefresh() },
  })
  const deleteQ = useMutation({
    mutationFn: adminApi.deleteQuizQuestion,
    onSuccess: () => { toast.success('Pregunta eliminada'); onRefresh() },
  })
  const createC = useMutation({
    mutationFn: adminApi.createChallenge,
    onSuccess: () => { toast.success('Desafío creado'); onRefresh(); setGenPreview(null) },
  })
  const deleteC = useMutation({
    mutationFn: adminApi.deleteChallenge,
    onSuccess: () => { toast.success('Desafío eliminado'); onRefresh() },
  })

  const generate = useMutation({
    mutationFn: ({ difficulty, level }: { difficulty: Difficulty; level: StudentLevel }) =>
      adminApi.generateChallenge(topic.id, difficulty, level).then((r) => r.data),
    onSuccess: (preview) => {
      setGenPreview(preview)
      toast.success('Desafío generado — revisa y aprueba')
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || 'Error al generar'),
  })

  const handleCreateQuestion = () => {
    const text = prompt('Texto de la pregunta:')
    if (!text) return
    const opts: string[] = []
    for (let i = 0; i < 4; i++) {
      const o = prompt(`Opción ${i + 1}:`)
      if (o === null) return
      opts.push(o)
    }
    const correctStr = prompt('Índice correcto (0-3):')
    const correct = Number(correctStr)
    if (![0, 1, 2, 3].includes(correct)) return toast.error('Índice inválido')
    const explanation = prompt('Explicación:') || ''
    createQ.mutate({
      topic_id: topic.id,
      question_text: text,
      options: opts,
      correct_option_index: correct,
      explanation,
      order_index: (questions?.length || 0),
    })
  }

  const handleGenerate = () => {
    const diff = prompt('Dificultad (easy/medium/hard):', 'medium') as Difficulty
    if (!['easy', 'medium', 'hard'].includes(diff)) return toast.error('Dificultad inválida')
    const lvl = prompt('Nivel objetivo (beginner/intermediate/advanced):', 'intermediate') as StudentLevel
    if (!['beginner', 'intermediate', 'advanced'].includes(lvl)) return toast.error('Nivel inválido')
    generate.mutate({ difficulty: diff, level: lvl })
  }

  const handleApprovePreview = () => {
    if (!genPreview) return
    createC.mutate({
      topic_id: topic.id,
      title: genPreview.title,
      description: genPreview.description,
      language: genPreview.language,
      difficulty: genPreview.difficulty,
      hints: genPreview.hints,
      solution_code: genPreview.solution_code,
      order_index: (challenges?.length || 0),
    })
  }

  return (
    <div className="px-4 py-3 border-t border-gray-100 bg-gray-50 space-y-4">
      {/* Quiz questions */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase text-gray-500 flex items-center gap-1">
            <HelpCircle className="w-3 h-3" /> Preguntas quiz (BD fallback)
          </span>
          <Button size="sm" variant="outline" onClick={handleCreateQuestion}>
            <Plus className="w-3 h-3 mr-1" /> Pregunta
          </Button>
        </div>
        {!questions || questions.length === 0 ? (
          <p className="text-xs text-gray-400 italic">Sin preguntas estáticas</p>
        ) : (
          <ul className="space-y-1">
            {questions.map((q) => (
              <li key={q.id} className="flex items-center justify-between text-xs bg-white px-3 py-2 rounded border border-gray-100">
                <span className="truncate flex-1 text-gray-700">{q.question_text}</span>
                <Button size="sm" variant="ghost" onClick={() => {
                  if (confirm('¿Eliminar pregunta?')) deleteQ.mutate(q.id)
                }}>
                  <Trash2 className="w-3 h-3 text-red-500" />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Coding challenges */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase text-gray-500 flex items-center gap-1">
            <Code2 className="w-3 h-3" /> Desafíos de código
          </span>
          <Button
            size="sm"
            variant="outline"
            onClick={handleGenerate}
            disabled={generate.isPending}
          >
            <Sparkles className="w-3 h-3 mr-1" />
            {generate.isPending ? 'Generando...' : 'Generar con IA'}
          </Button>
        </div>
        {!challenges || challenges.length === 0 ? (
          <p className="text-xs text-gray-400 italic">Sin desafíos</p>
        ) : (
          <ul className="space-y-1">
            {challenges.map((c) => (
              <li key={c.id} className="flex items-center justify-between text-xs bg-white px-3 py-2 rounded border border-gray-100">
                <span className="flex items-center gap-2 flex-1 truncate">
                  <span
                    className={cn(
                      'px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase',
                      c.difficulty === 'easy' && 'bg-green-100 text-green-700',
                      c.difficulty === 'medium' && 'bg-yellow-100 text-yellow-700',
                      c.difficulty === 'hard' && 'bg-red-100 text-red-700'
                    )}
                  >
                    {c.difficulty}
                  </span>
                  <span className="text-gray-700 truncate">{c.title}</span>
                </span>
                <Button size="sm" variant="ghost" onClick={() => {
                  if (confirm('¿Eliminar desafío?')) deleteC.mutate(c.id)
                }}>
                  <Trash2 className="w-3 h-3 text-red-500" />
                </Button>
              </li>
            ))}
          </ul>
        )}

        {genPreview && (
          <div className="mt-3 bg-white border-2 border-dashed border-primary-300 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-primary-700 uppercase">
                Vista previa IA (no guardada)
              </span>
              <Button size="sm" variant="ghost" onClick={() => setGenPreview(null)}>
                Descartar
              </Button>
            </div>
            <h4 className="font-semibold text-gray-900 text-sm mb-1">{genPreview.title}</h4>
            <pre className="text-[11px] bg-gray-50 p-2 rounded max-h-40 overflow-auto whitespace-pre-wrap mb-2">
              {genPreview.description.slice(0, 500)}
              {genPreview.description.length > 500 ? '...' : ''}
            </pre>
            <Button
              size="sm"
              onClick={handleApprovePreview}
              disabled={createC.isPending}
            >
              Aprobar y guardar
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
