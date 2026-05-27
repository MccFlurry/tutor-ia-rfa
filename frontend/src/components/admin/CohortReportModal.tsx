import type { StudentRow } from '@/types/adminReports'

interface Props {
  students: StudentRow[]
  onClose: () => void
}

export default function CohortReportModal({ onClose }: Props) {
  return (
    <div
      role="dialog"
      aria-label="Reporte cohorte IA"
      className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4"
    >
      <div className="bg-card border border-border rounded-xl p-6 max-w-2xl w-full">
        <p>Modal en construcción — ver Task 14.</p>
        <button
          type="button"
          onClick={onClose}
          className="mt-4 px-3 py-1 text-sm border border-border rounded"
        >
          Cerrar
        </button>
      </div>
    </div>
  )
}
