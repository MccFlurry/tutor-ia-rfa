import { useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, RefreshCw, Trash2, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { adminApi, type DocumentAdmin } from '@/api/admin'
import { Button } from '@/components/ui/button'

const STATUS_STYLE: Record<DocumentAdmin['status'], { label: string; cls: string; icon: React.ComponentType<{ className?: string }> }> = {
  pending: { label: 'Pendiente', cls: 'bg-gray-100 text-gray-700', icon: Loader2 },
  processing: { label: 'Procesando', cls: 'bg-blue-100 text-blue-700', icon: Loader2 },
  active: { label: 'Activo', cls: 'bg-green-100 text-green-700', icon: CheckCircle2 },
  error: { label: 'Error', cls: 'bg-red-100 text-red-700', icon: AlertCircle },
}

export default function CorpusTab() {
  const queryClient = useQueryClient()
  const fileInput = useRef<HTMLInputElement>(null)

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
          <h3 className="font-semibold text-gray-900">Documentos del corpus</h3>
          <p className="text-sm text-gray-500">PDF, DOCX, TXT, MD — máx 50 MB cada uno</p>
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

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Cargando...</div>
        ) : !data || data.length === 0 ? (
          <div className="p-8 text-center text-gray-500 text-sm">
            No hay documentos. Sube el primero para alimentar el corpus RAG.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
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
                  <tr key={doc.id} className="border-t border-gray-100">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-gray-400 shrink-0" />
                        <span className="font-medium text-gray-800 truncate max-w-xs">
                          {doc.original_filename}
                        </span>
                      </div>
                      {doc.error_message && (
                        <p className="text-xs text-red-500 mt-1">{doc.error_message}</p>
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
                    <td className="px-4 py-3 text-right text-gray-700">{doc.chunk_count}</td>
                    <td className="px-4 py-3 text-right text-gray-600 text-xs">
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
                          onClick={() => {
                            if (confirm(`¿Eliminar "${doc.original_filename}"?`)) {
                              remove.mutate(doc.id)
                            }
                          }}
                          disabled={remove.isPending}
                        >
                          <Trash2 className="w-3 h-3 text-red-500" />
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
    </div>
  )
}
