import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Pencil, Power } from 'lucide-react'
import toast from 'react-hot-toast'
import { adminApi, type AssessmentBankItem } from '@/api/admin'
import type { Difficulty } from '@/types/assessment'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const DIFF_COLOR: Record<Difficulty, string> = {
  easy: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  hard: 'bg-red-100 text-red-700',
}

export default function BankTab() {
  const queryClient = useQueryClient()
  const [moduleFilter, setModuleFilter] = useState<number | undefined>(undefined)
  const [diffFilter, setDiffFilter] = useState<Difficulty | undefined>(undefined)

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
    onSuccess: () => { toast.success('Pregunta agregada'); invalidate() },
    onError: () => toast.error('Error al crear'),
  })

  const updateItem = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => adminApi.updateBankItem(id, data),
    onSuccess: () => { toast.success('Actualizada'); invalidate() },
  })

  const deleteItem = useMutation({
    mutationFn: adminApi.deleteBankItem,
    onSuccess: () => { toast.success('Eliminada'); invalidate() },
  })

  const handleCreate = () => {
    if (!modules || modules.length === 0) return toast.error('Crea un módulo primero')
    const moduleStr = prompt(
      'module_id (existente):\n' + modules.map((m) => `  ${m.id}=${m.title}`).join('\n'),
      String(modules[0].id)
    )
    const module_id = Number(moduleStr)
    if (!Number.isInteger(module_id)) return
    const question_text = prompt('Texto de la pregunta:')
    if (!question_text) return
    const opts: string[] = []
    for (let i = 0; i < 4; i++) {
      const o = prompt(`Opción ${i + 1}:`)
      if (o === null) return
      opts.push(o)
    }
    const correctStr = prompt('Índice correcto (0-3):', '0')
    const correct_index = Number(correctStr)
    if (![0, 1, 2, 3].includes(correct_index)) return toast.error('Índice inválido')
    const difficulty = prompt('Dificultad (easy/medium/hard):', 'medium') as Difficulty
    if (!['easy', 'medium', 'hard'].includes(difficulty)) return toast.error('Dificultad inválida')

    createItem.mutate({
      module_id,
      question_text,
      options: opts,
      correct_index,
      difficulty,
    })
  }

  const handleEdit = (item: AssessmentBankItem) => {
    const text = prompt('Pregunta:', item.question_text)
    if (text === null) return
    updateItem.mutate({ id: item.id, data: { question_text: text } })
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
            className="text-sm border border-gray-200 rounded px-3 py-1.5"
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
            className="text-sm border border-gray-200 rounded px-3 py-1.5"
          >
            <option value="">Todas dificultades</option>
            <option value="easy">Fácil</option>
            <option value="medium">Media</option>
            <option value="hard">Difícil</option>
          </select>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="w-4 h-4 mr-1" />
          Nueva pregunta
        </Button>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-x-auto">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Cargando...</div>
        ) : !items || items.length === 0 ? (
          <div className="p-8 text-center text-gray-500 text-sm">
            Sin preguntas. El banco fallback es útil cuando Ollama no está disponible durante la evaluación de entrada.
          </div>
        ) : (
          <table className="w-full text-sm min-w-[640px]">
            <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
              <tr>
                <th className="px-4 py-3 text-left">Módulo</th>
                <th className="px-4 py-3 text-left">Pregunta</th>
                <th className="px-4 py-3 text-left">Dificultad</th>
                <th className="px-4 py-3 text-left">Estado</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-t border-gray-100">
                  <td className="px-4 py-3 text-gray-700">M{item.module_id}</td>
                  <td className="px-4 py-3 max-w-md truncate text-gray-800">
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
                    <span className={item.is_active ? 'text-green-600' : 'text-gray-400'}>
                      {item.is_active ? 'Activa' : 'Inactiva'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex gap-1 justify-end">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() =>
                          updateItem.mutate({
                            id: item.id,
                            data: { is_active: !item.is_active },
                          })
                        }
                      >
                        <Power className="w-3 h-3" />
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => handleEdit(item)}>
                        <Pencil className="w-3 h-3" />
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => {
                        if (confirm('¿Eliminar?')) deleteItem.mutate(item.id)
                      }}>
                        <Trash2 className="w-3 h-3 text-red-500" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
