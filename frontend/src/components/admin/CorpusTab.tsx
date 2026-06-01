import { useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, RefreshCw, Trash2, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { adminApi, type DocumentAdmin } from '@/api/admin'
import { Button } from '@/components/ui/button'
import EmptyState from '@/components/common/EmptyState'
import ConfirmDialog from '@/components/common/ConfirmDialog'

const STATUS_STYLE: Record<DocumentAdmin['status'], { label: string; cls: string; icon: React.ComponentType<{ className?: string }> }> = {
  pending: { label: 'Pendiente', cls: 'bg-muted text-muted-foreground', icon: Loader2 },
  processing: { label: 'Procesando', cls: 'bg-info/10 text-info', icon: Loader2 },
  active: { label: 'Activo', cls: 'bg-success/10 text-success', icon: CheckCircle2 },
  error: { label: 'Error', cls: 'bg-destructive/10 text-destructive', icon: AlertCircle },
}

interface DeleteDlg { open: boolean; id: string | null; label: string }

export default function CorpusTab() {
  const queryClient = useQueryClient()
  const fileInput = useRef<HTMLInputElement>(null)
  const [deleteDlg, setDeleteDlg] = useState<DeleteDlg>({ open: false, id: null, label: '' })

  const { data, isLoading } = useQuery({
    queryKey: ['admin', 'documents'],
    queryFn: () => adminApi.listDocuments().then((r) => r.data),
    refetchInterval: 5000, // auto-refresh while processing
  })

  const upload = useMutation({
    mutationFn: (file: File) => adminApi.uploadDocument(file),
    onSuccess: () => {
      toast.success('Documento subido. Procesando en segundo plano...')
      queryClient.invalidateQueries({ queryKey: ['admin', 'documents'] })
    },
    onError: (err: any) =>
      toast.error(err?.response?.data?.detail || 'Error al subir el documento'),
  })

  const reprocess = useMutation({
    mutationFn: (id: string) => adminApi.reprocessDocument(id),
    onSuccess: () => {
      toast.success('Reprocesando...')
      queryClient.invalidateQueries({ queryKey: ['admin', 'documents'] })
    },
    onError: () => toast.error('No se pudo reprocesar'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => adminApi.deleteDocument(id),
    onSuccess: () => {
      toast.success('Documento eliminado')
      queryClient.invalidateQueries({ queryKey: ['admin', 'documents'] })
      setDeleteDlg({ open: false, id: null, label: '' })
    },
    onError: () => toast.error('Error al eliminar'),
  })

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) upload.mutate(file)
    if (fileInput.current) fileInput.current.value = ''
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <div>
          <h3 className="font-semibold text-foreground">Documentos del corpus</h3>
          <p className="text-sm text-muted-foreground">PDF, DOCX, TXT, MD — máx 50 MB cada uno</p>
        </div>
        <div>
          <input
            ref={fileInput}
            type="file"
            accept=".pdf,.docx,.txt,.md"
            className="hidden"
            onChange={handleFile}
          />
          <Button onClick={() => fileInput.current?.click()} disabled={upload.isPending}>
            <Upload className="w-4 h-4 mr-2" />
            {upload.isPending ? 'Subiendo...' : 'Subir documento'}
          </Button>
        </div>
      </div>

      <div className="bg-card border border-border rounded-xl overflow-x-auto">
        {isLoading ? (
          <div className="p-6 space-y-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-10 bg-muted animate-pulse rounded" />
            ))}
          </div>
        ) : !data || data.length === 0 ? (
          <EmptyState
            icon={Upload}
            title="Sin documentos cargados"
            description="Sube documentos PDF, DOCX o MD para alimentar el corpus RAG."
            action={
              <button
                onClick={() => fileInput.current?.click()}
                disabled={upload.isPending}
                className="inline-flex items-center justify-center min-h-[44px] px-6 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                Subir documento
              </button>
            }
          />
        ) : (
          <table className="w-full text-sm min-w-[640px]">
            <thead className="bg-muted text-muted-foreground text-xs uppercase">
              <tr>
                <th className="px-4 py-3 text-left">Archivo</th>
                <th className="px-4 py-3 text-left">Estado</th>
                <th className="px-4 py-3 text-right">Chunks</th>
                <th className="px-4 py-3 text-right">Tamaño</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {data.map((doc) => {
                const style = STATUS_STYLE[doc.status]
                const Icon = style.icon
                return (
                  <tr key={doc.id} className="border-t border-border">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-muted-foreground shrink-0" />
                        <span className="font-medium text-foreground truncate max-w-xs">
                          {doc.original_filename}
                        </span>
                      </div>
                      {doc.error_message && (
                        <p className="text-xs text-destructive mt-1">{doc.error_message}</p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full ${style.cls}`}
                      >
                        <Icon
                          className={`w-3 h-3 ${
                            doc.status === 'processing' || doc.status === 'pending'
                              ? 'animate-spin'
                              : ''
                          }`}
                        />
                        {style.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-foreground">{doc.chunk_count}</td>
                    <td className="px-4 py-3 text-right text-muted-foreground text-xs">
                      {doc.file_size_bytes
                        ? `${(doc.file_size_bytes / 1024).toFixed(0)} KB`
                        : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1 justify-end">
                        {doc.status === 'error' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => reprocess.mutate(doc.id)}
                            disabled={reprocess.isPending}
                          >
                            <RefreshCw className="w-3 h-3 mr-1" />
                            Reintentar
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          aria-label={`Eliminar "${doc.original_filename}"`}
                          onClick={() =>
                            setDeleteDlg({ open: true, id: doc.id, label: doc.original_filename })
                          }
                          disabled={remove.isPending}
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

      <ConfirmDialog
        open={deleteDlg.open}
        onOpenChange={(o) => setDeleteDlg((s) => ({ ...s, open: o }))}
        title={`¿Eliminar "${deleteDlg.label}"?`}
        description="Se eliminarán también todos los chunks indexados de este documento. El RAG dejará de encontrar contenido en él."
        confirmLabel="Eliminar"
        destructive
        pending={remove.isPending}
        onConfirm={() => { if (deleteDlg.id !== null) remove.mutate(deleteDlg.id) }}
      />
    </div>
  )
}
