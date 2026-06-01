import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Pencil, Power, CheckCircle2, MinusCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { adminApi, type AssessmentBankItem } from '@/api/admin'
import type { Difficulty } from '@/types/assessment'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import FormDialog from '@/components/admin/FormDialog'
import ConfirmDialog from '@/components/common/ConfirmDialog'

const DIFF_COLOR: Record<Difficulty, string> = {
  easy: 'bg-success/10 text-success',
  medium: 'bg-warning/10 text-warning-foreground dark:text-warning',
  hard: 'bg-destructive/10 text-destructive',
}

interface CreateDlgState { open: boolean }
interface EditDlgState { open: boolean; target: AssessmentBankItem | null }
interface DeleteDlgState { open: boolean; id: number | null }

export default function BankTab() {
  const queryClient = useQueryClient()
  const [moduleFilter, setModuleFilter] = useState<number | undefined>(undefined)
  const [diffFilter, setDiffFilter] = useState<Difficulty | undefined>(undefined)
  const [createDlg, setCreateDlg] = useState<CreateDlgState>({ open: false })
  const [editDlg, setEditDlg] = useState<EditDlgState>({ open: false, target: null })
  const [deleteDlg, setDeleteDlg] = useState<DeleteDlgState>({ open: false, id: null })

  const { data: modules } = useQuery({
    queryKey: ['admin', 'modules'],
    queryFn: () => adminApi.listModules().then((r) => r.data),
  })

  const { data: items, isLoading } = useQuery({
    queryKey: ['admin', 'bank', moduleFilter, diffFilter],
    queryFn: () =>
      adminApi
        .listBank({ module_id: moduleFilter, difficulty: diffFilter })
        .then((r) => r.data),
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['admin', 'bank'] })
  }

  const createItem = useMutation({
    mutationFn: adminApi.createBankItem,
    onSuccess: () => { toast.success('Pregunta agregada'); invalidate(); setCreateDlg({ open: false }) },
    onError: () => toast.error('Error al crear'),
  })

  const updateItem = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => adminApi.updateBankItem(id, data),
    onSuccess: () => { toast.success('Actualizada'); invalidate(); setEditDlg({ open: false, target: null }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Error'),
  })

  const deleteItem = useMutation({
    mutationFn: adminApi.deleteBankItem,
    onSuccess: () => { toast.success('Eliminada'); invalidate(); setDeleteDlg({ open: false, id: null }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Error'),
  })

  // Build module id → title map for the table
  const moduleMap: Record<number, string> = {}
  if (modules) {
    for (const m of modules) moduleMap[m.id] = `${m.order_index}. ${m.title}`
  }

  const moduleOptions = (modules ?? []).map((m) => ({
    value: String(m.id),
    label: `${m.order_index}. ${m.title}`,
  }))

  const createFields = [
    {
      name: 'module_id',
      label: 'Módulo',
      type: 'select' as const,
      required: true,
      options: moduleOptions.length > 0 ? moduleOptions : [{ value: '', label: 'Sin módulos' }],
      defaultValue: moduleOptions[0]?.value ?? '',
    },
    { name: 'question_text', label: 'Texto de la pregunta', type: 'textarea' as const, required: true },
    { name: 'option_0', label: 'Opción 1', type: 'text' as const, required: true },
    { name: 'option_1', label: 'Opción 2', type: 'text' as const, required: true },
    { name: 'option_2', label: 'Opción 3', type: 'text' as const, required: true },
    { name: 'option_3', label: 'Opción 4', type: 'text' as const, required: true },
    {
      name: 'correct_index',
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
  ]

  const editFields = [
    {
      name: 'question_text',
      label: 'Texto de la pregunta',
      type: 'textarea' as const,
      required: true,
      defaultValue: editDlg.target?.question_text ?? '',
    },
  ]

  const handleCreate = (values: Record<string, string>) => {
    if (!modules || modules.length === 0) { toast.error('Crea un módulo primero'); return }
    const module_id = parseInt(values.module_id, 10)
    if (!Number.isInteger(module_id)) return
    const correct_index = parseInt(values.correct_index, 10)
    if (![0, 1, 2, 3].includes(correct_index)) { toast.error('Índice inválido'); return }
    const difficulty = values.difficulty as Difficulty
    createItem.mutate({
      module_id,
      question_text: values.question_text,
      options: [values.option_0, values.option_1, values.option_2, values.option_3],
      correct_index,
      difficulty,
    })
  }

  const handleEdit = (values: Record<string, string>) => {
    if (!editDlg.target) return
    updateItem.mutate({ id: editDlg.target.id, data: { question_text: values.question_text } })
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={moduleFilter ?? ''}
            onChange={(e) =>
              setModuleFilter(e.target.value ? Number(e.target.value) : undefined)
            }
            className="text-sm border border-border bg-background text-foreground rounded px-3 py-1.5"
          >
            <option value="">Todos los módulos</option>
            {modules?.map((m) => (
              <option key={m.id} value={m.id}>
                {m.order_index}. {m.title}
              </option>
            ))}
          </select>
          <select
            value={diffFilter ?? ''}
            onChange={(e) => setDiffFilter((e.target.value || undefined) as Difficulty | undefined)}
            className="text-sm border border-border bg-background text-foreground rounded px-3 py-1.5"
          >
            <option value="">Todas dificultades</option>
            <option value="easy">Fácil</option>
            <option value="medium">Media</option>
            <option value="hard">Difícil</option>
          </select>
        </div>
        <Button onClick={() => setCreateDlg({ open: true })}>
          <Plus className="w-4 h-4 mr-1" />
          Nueva pregunta
        </Button>
      </div>

      <div className="bg-card border border-border rounded-xl overflow-x-auto">
        {isLoading ? (
          <div className="p-6 space-y-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-10 bg-muted animate-pulse rounded" />
            ))}
          </div>
        ) : !items || items.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground text-sm">
            Sin preguntas. El banco fallback es útil cuando Ollama no está disponible durante la evaluación de entrada.
          </div>
        ) : (
          <table className="w-full text-sm min-w-[640px]">
            <thead className="bg-muted text-muted-foreground text-xs uppercase">
              <tr>
                <th className="px-4 py-3 text-left">Módulo</th>
                <th className="px-4 py-3 text-left">Pregunta</th>
                <th className="px-4 py-3 text-left">Dificultad</th>
                <th className="px-4 py-3 text-left">Estado</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const moduleLabel = moduleMap[item.module_id]
                return (
                  <tr key={item.id} className="border-t border-border">
                    <td
                      className="px-4 py-3 text-foreground"
                      title={moduleLabel ?? `Módulo ${item.module_id}`}
                    >
                      {moduleLabel ?? `M${item.module_id}`}
                    </td>
                    <td className="px-4 py-3 max-w-md truncate text-foreground">
                      {item.question_text}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={cn(
                          'text-xs font-semibold px-2 py-0.5 rounded uppercase',
                          DIFF_COLOR[item.difficulty]
                        )}
                      >
                        {item.difficulty}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs">
                      <span
                        className={cn(
                          'inline-flex items-center gap-1',
                          item.is_active ? 'text-success' : 'text-muted-foreground'
                        )}
                      >
                        {item.is_active ? (
                          <CheckCircle2 className="w-3 h-3 shrink-0" aria-hidden="true" />
                        ) : (
                          <MinusCircle className="w-3 h-3 shrink-0" aria-hidden="true" />
                        )}
                        {item.is_active ? 'Activa' : 'Inactiva'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex gap-1 justify-end">
                        <Button
                          size="sm"
                          variant="ghost"
                          aria-label={item.is_active ? 'Desactivar pregunta' : 'Activar pregunta'}
                          onClick={() =>
                            updateItem.mutate({
                              id: item.id,
                              data: { is_active: !item.is_active },
                            })
                          }
                        >
                          <Power className="w-3 h-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          aria-label="Editar pregunta"
                          onClick={() => setEditDlg({ open: true, target: item })}
                        >
                          <Pencil className="w-3 h-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          aria-label="Eliminar pregunta"
                          onClick={() => setDeleteDlg({ open: true, id: item.id })}
                        >
                          <Trash2 className="w-3 h-3 text-destructive" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Create dialog */}
      <FormDialog
        open={createDlg.open}
        onOpenChange={(o) => setCreateDlg({ open: o })}
        title="Nueva pregunta en banco fallback"
        fields={createFields}
        pending={createItem.isPending}
        onSubmit={handleCreate}
      />

      {/* Edit dialog */}
      <FormDialog
        open={editDlg.open}
        onOpenChange={(o) => setEditDlg((s) => ({ ...s, open: o }))}
        title="Editar pregunta"
        fields={editFields}
        pending={updateItem.isPending}
        onSubmit={handleEdit}
      />

      {/* Delete confirm */}
      <ConfirmDialog
        open={deleteDlg.open}
        onOpenChange={(o) => setDeleteDlg((s) => ({ ...s, open: o }))}
        title="¿Eliminar esta pregunta?"
        description="Se quitará del banco de evaluación de entrada."
        confirmLabel="Eliminar"
        destructive
        pending={deleteItem.isPending}
        onConfirm={() => { if (deleteDlg.id !== null) deleteItem.mutate(deleteDlg.id) }}
      />
    </div>
  )
}
