import { useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import toast from 'react-hot-toast'
import { Printer, Sparkles } from 'lucide-react'

import { adminReportsApi } from '@/api/adminReports'
import type { AIReport, RiskLevel } from '@/types/adminReports'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const RISK_STYLES: Record<RiskLevel, string> = {
  bajo: 'bg-success/10 text-success border-success/30',
  medio: 'bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-500/15 dark:text-amber-300',
  alto: 'bg-destructive/10 text-destructive border-destructive/30',
}

export default function AdminStudentReportPage() {
  const { userId = '' } = useParams<{ userId: string }>()

  const { data: detail, isLoading } = useQuery({
    queryKey: ['admin', 'student-detail', userId],
    queryFn: () => adminReportsApi.getDetail(userId).then((r) => r.data),
    enabled: Boolean(userId),
  })

  const mutation = useMutation<AIReport>({
    mutationFn: () => adminReportsApi.generateReport(userId).then((r) => r.data),
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail || 'No se pudo generar el reporte IA'),
  })

  if (isLoading || !detail) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="h-8 w-40 bg-muted animate-pulse rounded mb-4" />
        <div className="grid grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 bg-muted animate-pulse rounded" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6 printable-report">
      <header className="mb-6 flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground">{detail.full_name}</h1>
          <p className="text-sm text-muted-foreground">{detail.email}</p>
          {detail.level && (
            <span className="inline-block mt-2 px-2 py-0.5 text-xs font-semibold rounded bg-primary-100 text-primary-700">
              Nivel: {detail.level}
            </span>
          )}
          {detail.last_location && (
            <span className="block mt-1 text-xs text-muted-foreground">
              Última ubicación: {detail.last_location}
            </span>
          )}
        </div>
        <Button
          variant="ghost"
          onClick={() => window.print()}
          className="no-print"
        >
          <Printer className="w-4 h-4 mr-1" />
          Imprimir / PDF
        </Button>
      </header>

      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <Card label="Progreso global" value={`${detail.overall_progress_pct.toFixed(0)}%`} />
        <Card label="Tiempo invertido" value={`${Math.round(detail.total_time_seconds / 60)} min`} />
        <Card label="Mensajes al tutor" value={detail.chat_messages_count.toString()} />
        <Card label="Logros" value={detail.achievements_earned.length.toString()} />
      </section>

      <section className="mb-6">
        <h2 className="text-lg font-bold mb-3">Progreso por módulo</h2>
        <div className="space-y-2">
          {detail.modules.map((m) => (
            <div key={m.module_id} className="bg-card border border-border rounded-md p-3">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">{m.module_title}</span>
                <span className="text-muted-foreground">
                  {m.topics_completed}/{m.topics_total} temas
                </span>
              </div>
              <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary-500"
                  style={{ width: `${m.progress_pct}%` }}
                />
              </div>
              <div className="mt-1 text-xs text-muted-foreground flex gap-4">
                <span>Quiz: {m.avg_quiz_score !== null ? (m.avg_quiz_score * 100).toFixed(0) + '%' : '—'}</span>
                <span>Coding: {m.avg_coding_score !== null ? m.avg_coding_score.toFixed(0) : '—'}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="grid md:grid-cols-2 gap-6 mb-6">
        <RecentList
          title="Últimos quizzes"
          items={detail.recent_quizzes.map((q) => ({
            id: q.attempt_id,
            label: q.topic_title,
            score: `${(q.score * 100).toFixed(0)}%`,
            when: q.attempted_at,
          }))}
        />
        <RecentList
          title="Últimos desafíos de código"
          items={detail.recent_coding.map((c) => ({
            id: c.submission_id,
            label: c.challenge_title,
            score: `${c.score.toFixed(0)}/100`,
            when: c.submitted_at,
          }))}
        />
      </section>

      {detail.level_history.length > 0 && (
        <section className="mb-6">
          <h2 className="text-lg font-bold mb-3">Historial de nivel</h2>
          <ol className="space-y-2 text-sm">
            {detail.level_history.map((h, i) => (
              <li key={i} className="flex gap-4">
                <span className="text-muted-foreground w-32">
                  {new Date(h.changed_at).toLocaleDateString('es-PE')}
                </span>
                <span className="font-medium">{h.level}</span>
                <span className="text-muted-foreground">({h.score.toFixed(0)} pts)</span>
                {h.reason && <span className="text-xs text-muted-foreground">— {h.reason}</span>}
              </li>
            ))}
          </ol>
        </section>
      )}

      <section className="bg-card border border-border rounded-xl p-5">
        <div className="flex items-start justify-between flex-wrap gap-3 mb-3">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary-500" />
            Reporte IA
          </h2>
          <Button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="no-print"
          >
            {mutation.isPending ? 'La IA está analizando…' : 'Generar reporte'}
          </Button>
        </div>

        {mutation.data && (
          <article className="prose prose-sm dark:prose-invert max-w-none">
            <div className="flex items-center gap-2 mb-2">
              <span
                className={cn(
                  'px-2 py-0.5 text-xs font-semibold rounded border',
                  RISK_STYLES[mutation.data.risk_level],
                )}
              >
                Riesgo: {mutation.data.risk_level}
              </span>
              {mutation.data.cached && (
                <span className="text-xs text-muted-foreground">cacheado</span>
              )}
            </div>
            <ReactMarkdown>{mutation.data.summary}</ReactMarkdown>
            <p className="text-sm text-muted-foreground">
              <strong>Justificación:</strong> {mutation.data.risk_reason}
            </p>

            <h3>Fortalezas</h3>
            <ul>{mutation.data.strengths.map((s) => <li key={s}>{s}</li>)}</ul>

            <h3>Debilidades</h3>
            <ul>{mutation.data.weaknesses.map((s) => <li key={s}>{s}</li>)}</ul>

            <h3>Intervenciones sugeridas</h3>
            <ul>{mutation.data.interventions.map((s) => <li key={s}>{s}</li>)}</ul>
          </article>
        )}
      </section>
    </div>
  )
}

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-card border border-border rounded-md p-3">
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="text-xl font-bold text-foreground">{value}</div>
    </div>
  )
}

function RecentList({
  title,
  items,
}: {
  title: string
  items: { id: number; label: string; score: string; when: string }[]
}) {
  return (
    <div>
      <h2 className="text-lg font-bold mb-3">{title}</h2>
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">Sin registros.</p>
      ) : (
        <ul className="text-sm space-y-2">
          {items.map((it) => (
            <li key={it.id} className="flex items-center justify-between border-b border-border pb-1">
              <span className="truncate mr-2">{it.label}</span>
              <span className="font-semibold">{it.score}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
