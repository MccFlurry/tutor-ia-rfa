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
import FormDialog from '@/components/admin/FormDialog'
import ConfirmDialog from '@/components/common/ConfirmDialog'

// ---- Dialog state types ----

interface ModuleDialogState {
  open: boolean
  mode: 'create' | 'edit'
  target: ModuleAdmin | null
}

interface DeleteDialogState {
  open: boolean
  id: number | null
  label: string
}

// ---- ContentTab ----

export default function ContentTab() {
  const queryClient = useQueryClient()
  const [expandedModule, setExpandedModule] = useState<number | null>(null)
  const [expandedTopic, setExpandedTopic] = useState<number | null>(null)

  const [moduleDlg, setModuleDlg] = useState<ModuleDialogState>({
    open: false, mode: 'create', target: null,
  })
  const [deleteModuleDlg, setDeleteModuleDlg] = useState<DeleteDialogState>({
    open: false, id: null, label: '',
  })

  const { data: modules } = useQuery({
    queryKey: ['admin', 'modules'],
    queryFn: () => adminApi.listModules().then((r) => r.data),
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['admin'] })
  }

  const createModule = useMutation({
    mutationFn: adminApi.createModule,
    onSuccess: () => { toast.success('Módulo creado'); invalidate(); setModuleDlg((s) => ({ ...s, open: false })) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Error'),
  })
  const updateModule = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => adminApi.updateModule(id, data),
    onSuccess: () => { toast.success('Módulo actualizado'); invalidate(); setModuleDlg((s) => ({ ...s, open: false })) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Error'),
  })
  const deleteModule = useMutation({
    mutationFn: adminApi.deleteModule,
    onSuccess: () => {
      toast.success('Módulo eliminado')
      invalidate()
      setDeleteModuleDlg({ open: false, id: null, label: '' })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Error'),
  })

  const moduleFields = moduleDlg.mode === 'create'
    ? [
        { name: 'title', label: 'Título del módulo', type: 'text' as const, required: true, placeholder: 'Ej. Fundamentos de Android' },
        { name: 'order_index', label: 'Índice de orden', type: 'number' as const, required: true, defaultValue: String((modules?.length || 0) + 1), placeholder: '1' },
      ]
    : [
        { name: 'title', label: 'Título del módulo', type: 'text' as const, required: true, defaultValue: moduleDlg.target?.title ?? '' },
        { name: 'description', label: 'Descripción', type: 'textarea' as const, defaultValue: moduleDlg.target?.description ?? '', placeholder: 'Descripción opcional' },
      ]

  const handleModuleSubmit = (values: Record<string, string>) => {
    if (moduleDlg.mode === 'create') {
      const order_index = parseInt(values.order_index, 10)
      if (!Number.isInteger(order_index) || order_index < 1) {
        toast.error('Índice inválido')
        return
      }
      createModule.mutate({ title: values.title, order_index })
    } else if (moduleDlg.target) {
      updateModule.mutate({ id: moduleDlg.target.id, data: { title: values.title, description: values.description || '' } })
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-foreground">Árbol del curso</h3>
        <Button
          size="sm"
          onClick={() => setModuleDlg({ open: true, mode: 'create', target: null })}
        >
          <Plus className="w-4 h-4 mr-1" /> Módulo nuevo
        </Button>
      </div>

      {!modules || modules.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-8 text-center text-muted-foreground text-sm">
          Sin módulos aún.
        </div>
      ) : (
        <div className="space-y-2">
          {modules.map((m) => (
            <div key={m.id} className="bg-card border border-border rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 hover:bg-surface-hover">
                <button
                  onClick={() => setExpandedModule((prev) => (prev === m.id ? null : m.id))}
                  className="flex items-center gap-2 flex-1 min-w-0 text-left"
                >
                  {expandedModule === m.id ? (
                    <ChevronDown className="w-4 h-4 text-muted-foreground shrink-0" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />
                  )}
                  <span
                    className="w-6 h-6 rounded text-xs text-white flex items-center justify-center font-bold shrink-0"
                    style={{ backgroundColor: m.color_hex }}
                  >
                    {m.order_index}
                  </span>
                  <span className="font-medium text-foreground truncate">{m.title}</span>
                </button>
                <div className="flex gap-1 shrink-0">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setModuleDlg({ open: true, mode: 'edit', target: m })}
                    aria-label={`Editar módulo ${m.title}`}
                  >
                    <Pencil className="w-3 h-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setDeleteModuleDlg({ open: true, id: m.id, label: m.title })}
                    aria-label={`Eliminar módulo ${m.title}`}
                  >
                    <Trash2 className="w-3 h-3 text-destructive" />
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

      {/* Module form dialog */}
      <FormDialog
        open={moduleDlg.open}
        onOpenChange={(o) => setModuleDlg((s) => ({ ...s, open: o }))}
        title={moduleDlg.mode === 'create' ? 'Nuevo módulo' : 'Editar módulo'}
        fields={moduleFields}
        pending={createModule.isPending || updateModule.isPending}
        onSubmit={handleModuleSubmit}
      />

      {/* Delete module confirm */}
      <ConfirmDialog
        open={deleteModuleDlg.open}
        onOpenChange={(o) => setDeleteModuleDlg((s) => ({ ...s, open: o }))}
        title={`¿Eliminar módulo "${deleteModuleDlg.label}"?`}
        description="Se eliminarán también todos sus temas, preguntas y desafíos. Esta acción no se puede deshacer."
        confirmLabel="Eliminar"
        destructive
        pending={deleteModule.isPending}
        onConfirm={() => { if (deleteModuleDlg.id !== null) deleteModule.mutate(deleteModuleDlg.id) }}
      />
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
  const [topicDlg, setTopicDlg] = useState<{ open: boolean; mode: 'create' | 'edit'; target: TopicAdmin | null }>({
    open: false, mode: 'create', target: null,
  })
  const [deleteTopicDlg, setDeleteTopicDlg] = useState<{ open: boolean; id: number | null; label: string }>({
    open: false, id: null, label: '',
  })

  const { data: topics } = useQuery({
    queryKey: ['admin', 'topics', module.id],
    queryFn: () => adminApi.listTopics(module.id).then((r) => r.data),
  })

  const createTopic = useMutation({
    mutationFn: adminApi.createTopic,
    onSuccess: () => { toast.success('Tema creado'); onRefresh(); setTopicDlg((s) => ({ ...s, open: false })) },
    onError: () => toast.error('Error al crear tema'),
  })

  const updateTopic = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => adminApi.updateTopic(id, data),
    onSuccess: () => { toast.success('Tema actualizado'); onRefresh(); setTopicDlg((s) => ({ ...s, open: false })) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Error'),
  })

  const deleteTopic = useMutation({
    mutationFn: adminApi.deleteTopic,
    onSuccess: () => {
      toast.success('Tema eliminado')
      onRefresh()
      setDeleteTopicDlg({ open: false, id: null, label: '' })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Error'),
  })

  const topicFields = topicDlg.mode === 'create'
    ? [
        { name: 'title', label: 'Título del tema', type: 'text' as const, required: true, placeholder: 'Ej. Introducción a Kotlin' },
        { name: 'order_index', label: 'Orden', type: 'number' as const, required: true, defaultValue: String((topics?.length || 0) + 1) },
        { name: 'content', label: 'Contenido inicial (Markdown)', type: 'textarea' as const, placeholder: '# Título\n\nContenido...' },
        {
          name: 'has_quiz',
          label: '¿Este tema tiene autoevaluación?',
          type: 'select' as const,
          defaultValue: 'false',
          options: [
            { value: 'true', label: 'Sí' },
            { value: 'false', label: 'No' },
          ],
        },
      ]
    : [
        { name: 'title', label: 'Título del tema', type: 'text' as const, required: true, defaultValue: topicDlg.target?.title ?? '' },
      ]

  const handleTopicSubmit = (values: Record<string, string>) => {
    if (topicDlg.mode === 'create') {
      const order_index = parseInt(values.order_index, 10)
      if (!Number.isInteger(order_index) || order_index < 1) {
        toast.error('Orden inválido')
        return
      }
      createTopic.mutate({
        module_id: module.id,
        title: values.title,
        content: values.content || '',
        order_index,
        estimated_minutes: 15,
        has_quiz: values.has_quiz === 'true',
      })
    } else if (topicDlg.target) {
      updateTopic.mutate({ id: topicDlg.target.id, data: { title: values.title } })
    }
  }

  return (
    <div className="bg-muted px-4 py-3 border-t border-border">
      <div className="flex justify-between items-center mb-3">
        <span className="text-xs font-semibold uppercase text-muted-foreground">Temas</span>
        <Button
          size="sm"
          variant="outline"
          onClick={() => setTopicDlg({ open: true, mode: 'create', target: null })}
        >
          <Plus className="w-3 h-3 mr-1" /> Tema
        </Button>
      </div>
      {!topics || topics.length === 0 ? (
        <p className="text-xs text-muted-foreground italic">Sin temas</p>
      ) : (
        <div className="space-y-2">
          {topics.map((t) => (
            <div key={t.id} className="bg-card rounded-lg border border-border">
              <div className="flex items-center px-3 py-2 gap-2">
                <button
                  onClick={() => onToggleTopic(t.id)}
                  className="flex items-center gap-2 flex-1 text-left min-w-0"
                >
                  {expandedTopic === t.id ? (
                    <ChevronDown className="w-3 h-3 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="w-3 h-3 text-muted-foreground" />
                  )}
                  <FileText className="w-3 h-3 text-muted-foreground" />
                  <span className="text-sm text-foreground truncate">
                    {t.order_index}. {t.title}
                  </span>
                  {t.has_quiz && (
                    <span className="text-[10px] bg-info/10 text-info px-1.5 py-0.5 rounded">
                      Quiz
                    </span>
                  )}
                </button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setTopicDlg({ open: true, mode: 'edit', target: t })}
                  aria-label={`Editar tema ${t.title}`}
                >
                  <Pencil className="w-3 h-3" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setDeleteTopicDlg({ open: true, id: t.id, label: t.title })}
                  aria-label={`Eliminar tema ${t.title}`}
                >
                  <Trash2 className="w-3 h-3 text-destructive" />
                </Button>
              </div>
              {expandedTopic === t.id && <TopicDetail topic={t} onRefresh={onRefresh} />}
            </div>
          ))}
        </div>
      )}

      {/* Topic form dialog */}
      <FormDialog
        open={topicDlg.open}
        onOpenChange={(o) => setTopicDlg((s) => ({ ...s, open: o }))}
        title={topicDlg.mode === 'create' ? 'Nuevo tema' : 'Editar tema'}
        fields={topicFields}
        pending={createTopic.isPending || updateTopic.isPending}
        onSubmit={handleTopicSubmit}
      />

      {/* Delete topic confirm */}
      <ConfirmDialog
        open={deleteTopicDlg.open}
        onOpenChange={(o) => setDeleteTopicDlg((s) => ({ ...s, open: o }))}
        title={`¿Eliminar tema "${deleteTopicDlg.label}"?`}
        description="Se eliminarán también las preguntas y desafíos asociados."
        confirmLabel="Eliminar"
        destructive
        pending={deleteTopic.isPending}
        onConfirm={() => { if (deleteTopicDlg.id !== null) deleteTopic.mutate(deleteTopicDlg.id) }}
      />
    </div>
  )
}

// ---------- Topic Detail (quiz + coding lists) ----------

function TopicDetail({ topic, onRefresh }: { topic: TopicAdmin; onRefresh: () => void }) {
  const [genPreview, setGenPreview] = useState<GeneratedChallengePreview | null>(null)
  const [questionDlg, setQuestionDlg] = useState(false)
  const [generateDlg, setGenerateDlg] = useState(false)
  const [deleteQDlg, setDeleteQDlg] = useState<{ open: boolean; id: number | null }>({ open: false, id: null })
  const [deleteCDlg, setDeleteCDlg] = useState<{ open: boolean; id: number | null; label: string }>({ open: false, id: null, label: '' })

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
    onSuccess: () => { toast.success('Pregunta creada'); onRefresh(); setQuestionDlg(false) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Error'),
  })
  const deleteQ = useMutation({
    mutationFn: adminApi.deleteQuizQuestion,
    onSuccess: () => { toast.success('Pregunta eliminada'); onRefresh(); setDeleteQDlg({ open: false, id: null }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Error'),
  })
  const createC = useMutation({
    mutationFn: adminApi.createChallenge,
    onSuccess: () => { toast.success('Desafío creado'); onRefresh(); setGenPreview(null) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Error'),
  })
  const deleteC = useMutation({
    mutationFn: adminApi.deleteChallenge,
    onSuccess: () => { toast.success('Desafío eliminado'); onRefresh(); setDeleteCDlg({ open: false, id: null, label: '' }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Error'),
  })

  const generate = useMutation({
    mutationFn: ({ difficulty, level }: { difficulty: Difficulty; level: StudentLevel }) =>
      adminApi.generateChallenge(topic.id, difficulty, level).then((r) => r.data),
    onSuccess: (preview) => {
      setGenPreview(preview)
      toast.success('Desafío generado — revisa y aprueba')
      setGenerateDlg(false)
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || 'Error al generar'),
  })

  const handleQuestionSubmit = (values: Record<string, string>) => {
    const correct = parseInt(values.correct_option_index, 10)
    if (![0, 1, 2, 3].includes(correct)) {
      toast.error('Índice inválido')
      return
    }
    createQ.mutate({
      topic_id: topic.id,
      question_text: values.question_text,
      options: [values.option_0, values.option_1, values.option_2, values.option_3],
      correct_option_index: correct,
      explanation: values.explanation || '',
      order_index: questions?.length || 0,
    })
  }

  const handleGenerateSubmit = (values: Record<string, string>) => {
    const diff = values.difficulty as Difficulty
    const lvl = values.level as StudentLevel
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
      order_index: challenges?.length || 0,
    })
  }

  const questionFields = [
    { name: 'question_text', label: 'Texto de la pregunta', type: 'textarea' as const, required: true, placeholder: '¿Cuál es la salida de este código?' },
    { name: 'option_0', label: 'Opción 1', type: 'text' as const, required: true },
    { name: 'option_1', label: 'Opción 2', type: 'text' as const, required: true },
    { name: 'option_2', label: 'Opción 3', type: 'text' as const, required: true },
    { name: 'option_3', label: 'Opción 4', type: 'text' as const, required: true },
    {
      name: 'correct_option_index',
      label: 'Respuesta correcta',
      type: 'select' as const,
      required: true,
      defaultValue: '0',
      options: [
        { value: '0', label: 'Opción 1' },
        { value: '1', label: 'Opción 2' },
        { value: '2', label: 'Opción 3' },
        { value: '3', label: 'Opción 4' },
      ],
    },
    { name: 'explanation', label: 'Explicación', type: 'textarea' as const, placeholder: 'Explica por qué esta es la respuesta correcta...' },
  ]

  const generateFields = [
    {
      name: 'difficulty',
      label: 'Dificultad',
      type: 'select' as const,
      required: true,
      defaultValue: 'medium',
      options: [
        { value: 'easy', label: 'Fácil' },
        { value: 'medium', label: 'Media' },
        { value: 'hard', label: 'Difícil' },
      ],
    },
    {
      name: 'level',
      label: 'Nivel objetivo',
      type: 'select' as const,
      required: true,
      defaultValue: 'intermediate',
      options: [
        { value: 'beginner', label: 'Principiante' },
        { value: 'intermediate', label: 'Intermedio' },
        { value: 'advanced', label: 'Avanzado' },
      ],
    },
  ]

  return (
    <div className="px-4 py-3 border-t border-border bg-muted space-y-4">
      {/* Quiz questions */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase text-muted-foreground flex items-center gap-1">
            <HelpCircle className="w-3 h-3" /> Preguntas quiz (BD fallback)
          </span>
          <Button size="sm" variant="outline" onClick={() => setQuestionDlg(true)}>
            <Plus className="w-3 h-3 mr-1" /> Pregunta
          </Button>
        </div>
        {!questions || questions.length === 0 ? (
          <p className="text-xs text-muted-foreground italic">Sin preguntas estáticas</p>
        ) : (
          <ul className="space-y-1">
            {questions.map((q) => (
              <li key={q.id} className="flex items-center justify-between text-xs bg-card px-3 py-2 rounded border border-border">
                <span className="truncate flex-1 text-foreground">{q.question_text}</span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setDeleteQDlg({ open: true, id: q.id })}
                  aria-label="Eliminar pregunta"
                >
                  <Trash2 className="w-3 h-3 text-destructive" />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Coding challenges */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase text-muted-foreground flex items-center gap-1">
            <Code2 className="w-3 h-3" /> Desafíos de código
          </span>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setGenerateDlg(true)}
            disabled={generate.isPending}
          >
            <Sparkles className="w-3 h-3 mr-1" />
            {generate.isPending ? 'Generando...' : 'Generar con IA'}
          </Button>
        </div>
        {!challenges || challenges.length === 0 ? (
          <p className="text-xs text-muted-foreground italic">Sin desafíos</p>
        ) : (
          <ul className="space-y-1">
            {challenges.map((c) => (
              <li key={c.id} className="flex items-center justify-between text-xs bg-card px-3 py-2 rounded border border-border">
                <span className="flex items-center gap-2 flex-1 truncate">
                  <span
                    className={cn(
                      'px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase',
                      c.difficulty === 'easy' && 'bg-success/10 text-success',
                      c.difficulty === 'medium' && 'bg-warning/10 text-warning-foreground dark:text-warning',
                      c.difficulty === 'hard' && 'bg-destructive/10 text-destructive'
                    )}
                  >
                    {c.difficulty}
                  </span>
                  <span className="text-foreground truncate">{c.title}</span>
                </span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setDeleteCDlg({ open: true, id: c.id, label: c.title })}
                  aria-label={`Eliminar desafío ${c.title}`}
                >
                  <Trash2 className="w-3 h-3 text-destructive" />
                </Button>
              </li>
            ))}
          </ul>
        )}

        {genPreview && (
          <div className="mt-3 bg-card border-2 border-dashed border-primary-300 dark:border-primary-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-primary-700 dark:text-primary-300 uppercase">
                Vista previa IA (no guardada)
              </span>
              <Button size="sm" variant="ghost" onClick={() => setGenPreview(null)}>
                Descartar
              </Button>
            </div>
            <h4 className="font-semibold text-foreground text-sm mb-1">{genPreview.title}</h4>
            <pre className="text-[11px] bg-muted p-2 rounded max-h-40 overflow-auto whitespace-pre-wrap mb-2">
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

      {/* Question form dialog */}
      <FormDialog
        open={questionDlg}
        onOpenChange={setQuestionDlg}
        title="Nueva pregunta de quiz"
        fields={questionFields}
        pending={createQ.isPending}
        onSubmit={handleQuestionSubmit}
      />

      {/* Generate challenge dialog */}
      <FormDialog
        open={generateDlg}
        onOpenChange={setGenerateDlg}
        title="Generar desafío con IA"
        fields={generateFields}
        submitLabel="Generar"
        pending={generate.isPending}
        onSubmit={handleGenerateSubmit}
      />

      {/* Delete question confirm */}
      <ConfirmDialog
        open={deleteQDlg.open}
        onOpenChange={(o) => setDeleteQDlg((s) => ({ ...s, open: o }))}
        title="¿Eliminar esta pregunta?"
        confirmLabel="Eliminar"
        destructive
        pending={deleteQ.isPending}
        onConfirm={() => { if (deleteQDlg.id !== null) deleteQ.mutate(deleteQDlg.id) }}
      />

      {/* Delete challenge confirm */}
      <ConfirmDialog
        open={deleteCDlg.open}
        onOpenChange={(o) => setDeleteCDlg((s) => ({ ...s, open: o }))}
        title={`¿Eliminar desafío "${deleteCDlg.label}"?`}
        confirmLabel="Eliminar"
        destructive
        pending={deleteC.isPending}
        onConfirm={() => { if (deleteCDlg.id !== null) deleteC.mutate(deleteCDlg.id) }}
      />
    </div>
  )
}
