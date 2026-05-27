import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'

import { adminReportsApi } from '@/api/adminReports'
import type { StudentRow, CohortAIReport } from '@/types/adminReports'
import { Button } from '@/components/ui/button'

interface Props {
  students: StudentRow[]
  onClose: () => void
}

export default function CohortReportModal({ students, onClose }: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [report, setReport] = useState<CohortAIReport | null>(null)

  const mutation = useMutation({
    mutationFn: () =>
      adminReportsApi
        .generateCohortReport(Array.from(selected))
        .then((r) => r.data),
    onSuccess: (data) => setReport(data),
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || 'No se pudo generar el reporte'),
  })

  function toggle(id: string) {
    setSelected((s) => {
      const next = new Set(s)
      if (next.has(id)) next.delete(id)
      else if (next.size < 15) next.add(id)
      else toast.error('Máximo 15 estudiantes para el grupo')
      return next
    })
  }

  const canGenerate = selected.size >= 2 && selected.size <= 15 && !mutation.isPending

  return (
    <div
      role="dialog"
      aria-label="Reporte de grupo IA"
      className="fixed inset-0 z-50 grid place-items-center bg-black/50 p-4"
    >
      <div className="bg-card border border-border rounded-xl p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-foreground">Reporte de grupo IA</h2>
            <p className="text-sm text-muted-foreground">
              Selecciona entre 2 y 15 estudiantes.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-sm text-muted-foreground hover:text-foreground"
            aria-label="Cerrar"
          >
            Cerrar
          </button>
        </div>

        {!report && (
          <>
            <div className="border border-border rounded-md max-h-72 overflow-y-auto mb-4">
              {students.map((s) => (
                <label
                  key={s.user_id}
                  className="flex items-center gap-3 px-3 py-2 text-sm border-b border-border last:border-b-0 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selected.has(s.user_id)}
                    onChange={() => toggle(s.user_id)}
                    aria-label={s.full_name}
                  />
                  <span className="flex-1">{s.full_name}</span>
                  <span className="text-xs text-muted-foreground">{s.level ?? '—'}</span>
                </label>
              ))}
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={onClose} disabled={mutation.isPending}>
                Cancelar
              </Button>
              <Button
                onClick={() => mutation.mutate()}
                disabled={!canGenerate}
              >
                {mutation.isPending
                  ? 'La IA está analizando…'
                  : 'Generar reporte'}
              </Button>
            </div>
          </>
        )}

        {report && (
          <article className="prose prose-sm dark:prose-invert max-w-none">
            <h3>Narrativa</h3>
            <p>{report.narrative}</p>

            <h3>Destacan</h3>
            <ul>{report.top_performers.map((n) => <li key={n}>{n}</li>)}</ul>

            <h3>Requieren apoyo</h3>
            <ul>{report.needs_support.map((n) => <li key={n}>{n}</li>)}</ul>

            {report.common_gaps.length > 0 && (
              <>
                <h3>Brechas comunes</h3>
                <ul>{report.common_gaps.map((g) => <li key={g}>{g}</li>)}</ul>
              </>
            )}

            <h3>Recomendaciones</h3>
            <ul>{report.recommendations.map((r) => <li key={r}>{r}</li>)}</ul>

            <div className="flex justify-end mt-4 gap-2">
              <Button variant="ghost" onClick={() => setReport(null)}>
                Nueva selección
              </Button>
              <Button onClick={onClose}>Cerrar</Button>
            </div>
          </article>
        )}
      </div>
    </div>
  )
}
