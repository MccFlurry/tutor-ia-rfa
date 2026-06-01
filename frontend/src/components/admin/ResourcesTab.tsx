import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Power, ExternalLink, CheckCircle2, MinusCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { adminApi } from '@/api/admin'
import type { LearningResource, ResourceKind } from '@/types/resource'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import FormDialog from '@/components/admin/FormDialog'
import ConfirmDialog from '@/components/common/ConfirmDialog'

const KINDS: ResourceKind[] = ['video', 'book', 'article', 'doc']

interface DeleteDlgState { open: boolean; id: number | null; label: string }

export default function ResourcesTab() {
  const queryClient = useQueryClient()
  const [moduleFilter, setModuleFilter] = useState<number | undefined>(undefined)
  const [createDlg, setCreateDlg] = useState(false)
  const [deleteDlg, setDeleteDlg] = useState<DeleteDlgState>({ open: false, id: null, label: '' })

  const { data: modules } = useQuery({
    queryKey: ['admin', 'modules'],
    queryFn: () => adminApi.listModules().then((r) => r.data),
  })

  const { data: items, isLoading } = useQuery({
    queryKey: ['admin', 'resources', moduleFilter],
    queryFn: () =>
      adminApi.listResources({ module_id: moduleFilter }).then((r) => r.data),
  })

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ['admin', 'resources'] })

  const createItem = useMutation({
    mutationFn: adminApi.createResource,
    onSuccess: () => { toast.success('Recurso agregado'); invalidate(); setCreateDlg(false) },
    onError: () => toast.error('Error al crear'),
  })

  const updateItem = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<LearningResource> }) =>
      adminApi.updateResource(id, data),
    onSuccess: () => { toast.success('Actualizado'); invalidate() },
    onError: () => toast.error('Error al actualizar'),
  })

  const deleteItem = useMutation({
    mutationFn: adminApi.deleteResource,
    onSuccess: () => { toast.success('Eliminado'); invalidate(); setDeleteDlg({ open: false, id: null, label: '' }) },
    onError: () => toast.error('Error al eliminar'),
  })

  const moduleOptions = (modules ?? []).map((m) => ({
    value: String(m.id),
    label: `${m.order_index}. ${m.title}`,
  }))

  const createFields = [
    {
      name: 'kind',
      label: 'Tipo de recurso',
      type: 'select' as const,
      required: true,
      defaultValue: 'video',
      options: KINDS.map((k) => ({ value: k, label: k.charAt(0).toUpperCase() + k.slice(1) })),
    },
    { name: 'title', label: 'Título', type: 'text' as const, required: true },
    {
      name: 'url',
      label: 'URL',
      type: 'text' as const,
      required: true,
      placeholder: 'https://...',
      helpText: 'Verifica que la URL sea correcta antes de guardar. El sistema no genera enlaces automáticamente.',
    },
    {
      name: 'module_id',
      label: 'Módulo (opcional)',
      type: 'select' as const,
      defaultValue: moduleOptions[0]?.value ?? '',
      options: [
        { value: '', label: '— General (sin módulo) —' },
        ...moduleOptions,
      ],
    },
    { name: 'author', label: 'Autor (opcional)', type: 'text' as const, placeholder: 'Nombre del autor o institución' },
  ]

  const handleCreate = (values: Record<string, string>) => {
    const kind = values.kind as ResourceKind
    const module_id = values.module_id ? Number(values.module_id) : undefined
    createItem.mutate({
      kind,
      title: values.title,
      url: values.url,
      module_id,
      author: values.author || undefined,
    })
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <select
          value={moduleFilter ?? ''}
          onChange={(e) => setModuleFilter(e.target.value ? Number(e.target.value) : undefined)}
          className="text-sm border border-border bg-background text-foreground rounded px-3 py-1.5"
        >
          <option value="">Todos los módulos</option>
          {modules?.map((m) => (
            <option key={m.id} value={m.id}>
              {m.order_index}. {m.title}
            </option>
          ))}
        </select>
        <Button onClick={() => setCreateDlg(true)}>
          <Plus className="w-4 h-4 mr-1" />
          Nuevo recurso
        </Button>
      </div>

      <p className="text-xs text-muted-foreground mb-3">
        Los recursos son curados manualmente. Verifica cada URL antes de publicarla — el sistema no genera enlaces automáticamente.
      </p>

      <div className="bg-card border border-border rounded-xl overflow-x-auto">
        {isLoading ? (
          <div className="p-6 space-y-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-10 bg-muted animate-pulse rounded" />
            ))}
          </div>
        ) : !items || items.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground text-sm">
            Sin recursos. Agrega videos o libros para reforzar el aprendizaje.
          </div>
        ) : (
          <table className="w-full text-sm min-w-[640px]">
            <thead className="bg-muted text-muted-foreground text-xs uppercase">
              <tr>
                <th className="px-4 py-3 text-left">Módulo</th>
                <th className="px-4 py-3 text-left">Tipo</th>
                <th className="px-4 py-3 text-left">Título</th>
                <th className="px-4 py-3 text-left">Estado</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-t border-border">
                  <td className="px-4 py-3 text-foreground">
                    {item.module_id ? `M${item.module_id}` : '—'}
                  </td>
                  <td className="px-4 py-3 text-foreground uppercase text-xs">{item.kind}</td>
                  <td className="px-4 py-3 max-w-md truncate text-foreground">
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 hover:underline"
                    >
                      {item.title}
                      <ExternalLink className="w-3 h-3" />
                    </a>
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
                      {item.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex gap-1 justify-end">
                      <Button
                        size="sm"
                        variant="ghost"
                        aria-label={item.is_active ? 'Desactivar recurso' : 'Activar recurso'}
                        onClick={() =>
                          updateItem.mutate({ id: item.id, data: { is_active: !item.is_active } })
                        }
                      >
                        <Power className="w-3 h-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        aria-label={`Eliminar recurso "${item.title}"`}
                        onClick={() => setDeleteDlg({ open: true, id: item.id, label: item.title })}
                      >
                        <Trash2 className="w-3 h-3 text-destructive" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Create dialog */}
      <FormDialog
        open={createDlg}
        onOpenChange={setCreateDlg}
        title="Nuevo recurso de aprendizaje"
        fields={createFields}
        pending={createItem.isPending}
        onSubmit={handleCreate}
      />

      {/* Delete confirm */}
      <ConfirmDialog
        open={deleteDlg.open}
        onOpenChange={(o) => setDeleteDlg((s) => ({ ...s, open: o }))}
        title={`¿Eliminar "${deleteDlg.label}"?`}
        description="El recurso dejará de aparecer en el curso."
        confirmLabel="Eliminar"
        destructive
        pending={deleteItem.isPending}
        onConfirm={() => { if (deleteDlg.id !== null) deleteItem.mutate(deleteDlg.id) }}
      />
    </div>
  )
}
