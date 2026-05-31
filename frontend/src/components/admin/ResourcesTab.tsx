import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Power, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'
import { adminApi } from '@/api/admin'
import type { LearningResource, ResourceKind } from '@/types/resource'
import { Button } from '@/components/ui/button'

const KINDS: ResourceKind[] = ['video', 'book', 'article', 'doc']

export default function ResourcesTab() {
  const queryClient = useQueryClient()
  const [moduleFilter, setModuleFilter] = useState<number | undefined>(undefined)

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
    onSuccess: () => { toast.success('Recurso agregado'); invalidate() },
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
    onSuccess: () => { toast.success('Eliminado'); invalidate() },
    onError: () => toast.error('Error al eliminar'),
  })

  const handleCreate = () => {
    const kind = prompt('Tipo (video/book/article/doc):', 'video') as ResourceKind
    if (!KINDS.includes(kind)) return toast.error('Tipo inválido')
    const title = prompt('Título:')
    if (!title) return
    const url = prompt('URL (verifica que sea correcta):')
    if (!url) return
    const moduleStr = prompt(
      'module_id (opcional, vacío = general):',
      moduleFilter ? String(moduleFilter) : ''
    )
    const module_id = moduleStr ? Number(moduleStr) : undefined
    const author = prompt('Autor (opcional):') || undefined
    createItem.mutate({ kind, title, url, module_id, author })
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
        <Button onClick={handleCreate}>
          <Plus className="w-4 h-4 mr-1" />
          Nuevo recurso
        </Button>
      </div>

      <p className="text-xs text-muted-foreground mb-3">
        Los recursos son curados manualmente. Verifica cada URL antes de publicarla — el sistema no genera enlaces automáticamente.
      </p>

      <div className="bg-card border border-border rounded-xl overflow-x-auto">
        {isLoading ? (
          <div className="p-8 text-center text-muted-foreground">Cargando...</div>
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
                    <span className={item.is_active ? 'text-success' : 'text-muted-foreground'}>
                      {item.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex gap-1 justify-end">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() =>
                          updateItem.mutate({ id: item.id, data: { is_active: !item.is_active } })
                        }
                      >
                        <Power className="w-3 h-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          if (confirm('¿Eliminar?')) deleteItem.mutate(item.id)
                        }}
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
    </div>
  )
}
