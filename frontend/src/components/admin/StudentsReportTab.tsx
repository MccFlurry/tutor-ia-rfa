import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronRight, ChevronUp, Users2 } from 'lucide-react'

import { adminReportsApi } from '@/api/adminReports'
import type { StudentRow } from '@/types/adminReports'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import CohortReportModal from './CohortReportModal'

type SortKey =
  | 'full_name' | 'email' | 'level'
  | 'overall_progress_pct' | 'avg_quiz_score'
  | 'avg_coding_score' | 'last_activity_at'

const COLUMNS: { key: SortKey; label: string }[] = [
  { key: 'full_name', label: 'Nombre' },
  { key: 'email', label: 'Email' },
  { key: 'level', label: 'Nivel' },
  { key: 'overall_progress_pct', label: 'Progreso' },
  { key: 'avg_quiz_score', label: 'Promedio Quiz' },
  { key: 'avg_coding_score', label: 'Promedio Coding' },
  { key: 'last_activity_at', label: 'Última actividad' },
]

function compareRows(a: StudentRow, b: StudentRow, key: SortKey, dir: 1 | -1): number {
  const av = a[key]
  const bv = b[key]
  if (av === bv) return 0
  if (av === null || av === undefined) return 1
  if (bv === null || bv === undefined) return -1
  return (av > bv ? 1 : -1) * dir
}

export default function StudentsReportTab() {
  const navigate = useNavigate()
  const [sortKey, setSortKey] = useState<SortKey>('full_name')
  const [sortDir, setSortDir] = useState<1 | -1>(1)
  const [levelFilter, setLevelFilter] = useState<string>('')
  const [search, setSearch] = useState<string>('')
  const [includeInactive, setIncludeInactive] = useState(false)
  const [cohortOpen, setCohortOpen] = useState(false)

  const { data: rows = [], isLoading } = useQuery({
    queryKey: ['admin', 'students-report'],
    queryFn: () => adminReportsApi.listStudents().then((r) => r.data),
  })

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return rows
      .filter((r) => (includeInactive ? true : r.is_active))
      .filter((r) => (levelFilter ? r.level === levelFilter : true))
      .filter((r) =>
        q ? r.full_name.toLowerCase().includes(q) || r.email.toLowerCase().includes(q) : true
      )
      .sort((a, b) => compareRows(a, b, sortKey, sortDir))
  }, [rows, levelFilter, search, includeInactive, sortKey, sortDir])

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === 1 ? -1 : 1))
    } else {
      setSortKey(key)
      setSortDir(-1)
    }
  }

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <input
          type="search"
          placeholder="Buscar nombre o email"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-9 px-3 text-sm border border-border bg-background rounded-md min-w-[200px]"
        />
        <label className="flex items-center gap-2 text-sm">
          <span className="sr-only">Filtrar por nivel</span>
          <select
            aria-label="Filtrar por nivel"
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="h-9 px-2 text-sm border border-border bg-background rounded-md"
          >
            <option value="">Todos los niveles</option>
            <option value="beginner">Principiante</option>
            <option value="intermediate">Intermedio</option>
            <option value="advanced">Avanzado</option>
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={(e) => setIncludeInactive(e.target.checked)}
          />
          Incluir inactivos
        </label>
        <div className="ml-auto">
          <Button onClick={() => setCohortOpen(true)} variant="default" size="sm">
            <Users2 className="w-4 h-4 mr-1" />
            Reporte de grupo IA
          </Button>
        </div>
      </div>

      <div className="bg-card border border-border rounded-xl overflow-x-auto">
        {isLoading ? (
          <div className="p-6 space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-10 bg-muted animate-pulse rounded" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground text-sm">
            No hay estudiantes que coincidan con los filtros.
          </div>
        ) : (
          <table className="w-full text-sm min-w-[860px]">
            <thead className="bg-muted text-muted-foreground text-xs uppercase">
              <tr>
                {COLUMNS.map((c) => {
                  const isActive = sortKey === c.key
                  const ariaSort = isActive
                    ? sortDir === 1
                      ? ('ascending' as const)
                      : ('descending' as const)
                    : ('none' as const)
                  return (
                    <th
                      key={c.key}
                      scope="col"
                      aria-sort={ariaSort}
                      className="px-4 py-3 text-left"
                    >
                      <button
                        type="button"
                        onClick={() => toggleSort(c.key)}
                        className="inline-flex items-center gap-1 font-semibold uppercase tracking-wide hover:text-foreground"
                      >
                        {c.label}
                        {isActive ? (
                          sortDir === 1 ? (
                            <ChevronUp aria-hidden="true" className="w-3 h-3 shrink-0" />
                          ) : (
                            <ChevronDown aria-hidden="true" className="w-3 h-3 shrink-0" />
                          )
                        ) : null}
                      </button>
                    </th>
                  )
                })}
                {/* trailing header for the chevron affordance column */}
                <th scope="col" className="px-4 py-3 w-8" aria-hidden="true" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => {
                const dest = `/admin/students/${r.user_id}`
                return (
                  <tr
                    key={r.user_id}
                    onClick={() => navigate(dest)}
                    className={cn(
                      'border-t border-border cursor-pointer hover:bg-muted/50 focus-within:bg-muted/50',
                      !r.is_active && 'opacity-60'
                    )}
                  >
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate(dest)
                        }}
                        className="font-medium text-foreground text-left hover:underline rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        aria-label={`Ver detalle de ${r.full_name}`}
                      >
                        {r.full_name}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{r.email}</td>
                    <td className="px-4 py-3">{r.level ?? '—'}</td>
                    <td className="px-4 py-3">{r.overall_progress_pct.toFixed(0)}%</td>
                    <td className="px-4 py-3">
                      {r.avg_quiz_score !== null ? (r.avg_quiz_score * 100).toFixed(0) + '%' : '—'}
                    </td>
                    <td className="px-4 py-3">
                      {r.avg_coding_score !== null ? r.avg_coding_score.toFixed(0) : '—'}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {r.last_activity_at
                        ? new Date(r.last_activity_at).toLocaleString('es-PE')
                        : 'sin actividad'}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground" aria-hidden="true">
                      <ChevronRight className="w-4 h-4" />
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {cohortOpen && (
        <CohortReportModal students={filtered} onClose={() => setCohortOpen(false)} />
      )}
    </div>
  )
}
