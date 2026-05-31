import { Link } from 'react-router-dom'
import { Lock, Check } from 'lucide-react'
import * as LucideIcons from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { Module } from '@/types/module'

interface ModuleCardProps {
  module: Module
}

function getIcon(iconName: string | null) {
  if (!iconName) return LucideIcons.BookOpen
  const pascal = iconName
    .split('-')
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join('')
  return (LucideIcons as Record<string, any>)[pascal] || LucideIcons.BookOpen
}

type StatusVariant = 'default' | 'secondary' | 'outline' | 'success'

// Route-state language (DESIGN.md): locked = muted, not-started = neutral outline,
// in-progress = blue (the current step), completed = green + a check.
function getStatusBadge(module: Module): { label: string; variant: StatusVariant; check?: boolean } {
  if (module.is_locked) return { label: 'Bloqueado', variant: 'secondary' }
  if (module.progress_pct >= 100) return { label: 'Completado', variant: 'success', check: true }
  if (module.progress_pct > 0) return { label: 'En progreso', variant: 'default' }
  return { label: 'No iniciado', variant: 'outline' }
}

const LOCKED_REASON = 'Completa el módulo anterior para desbloquear este contenido.'

export default function ModuleCard({ module }: ModuleCardProps) {
  const Icon = getIcon(module.icon_name)
  const status = getStatusBadge(module)
  const locked = module.is_locked
  const completed = !locked && module.progress_pct >= 100

  const ariaLabel = locked
    ? `${module.title} — Bloqueado. ${LOCKED_REASON}`
    : `${module.title} — ${Math.round(module.progress_pct)}% completado`

  const content = (
    <>
      {/* Icon + Badge row */}
      <div className="flex items-start justify-between mb-4">
        <div
          className={cn(
            'w-12 h-12 rounded-lg flex items-center justify-center',
            locked && 'bg-muted'
          )}
          style={!locked ? { backgroundColor: `${module.color_hex}20` } : undefined}
          aria-hidden="true"
        >
          {locked ? (
            <Lock className="w-6 h-6 text-muted-foreground" />
          ) : (
            <Icon className="w-6 h-6" style={{ color: module.color_hex }} />
          )}
        </div>
        <Badge variant={status.variant}>
          {status.check && <Check className="w-3 h-3 mr-1" aria-hidden="true" />}
          {status.label}
        </Badge>
      </div>

      {/* Title + Description */}
      <h3
        className={cn(
          'font-semibold mb-1 line-clamp-2',
          locked ? 'text-muted-foreground' : 'text-foreground'
        )}
      >
        {module.title}
      </h3>
      {module.description && (
        <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
          {module.description}
        </p>
      )}

      {locked ? (
        /* Locked: explain why, no progress bar to compete with the message */
        <div
          className="flex items-start gap-2 text-xs text-muted-foreground bg-muted/50 rounded-lg p-2.5"
          role="note"
        >
          <Lock className="w-3.5 h-3.5 shrink-0 mt-0.5" aria-hidden="true" />
          <span>{LOCKED_REASON}</span>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-muted-foreground tabular-nums">
            <span>
              {module.completed_topics} de {module.total_topics} temas
            </span>
            <span>{Math.round(module.progress_pct)}%</span>
          </div>
          <Progress
            value={module.progress_pct}
            className="h-2"
            indicatorClassName={completed ? 'bg-success' : undefined}
          />
        </div>
      )}
    </>
  )

  const baseClasses =
    'relative block rounded-xl border p-6 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2'

  if (locked) {
    return (
      <article
        aria-label={ariaLabel}
        aria-disabled="true"
        title={LOCKED_REASON}
        className={cn(baseClasses, 'bg-muted/40 border-border cursor-not-allowed select-none')}
      >
        {content}
      </article>
    )
  }

  return (
    <Link
      to={`/modules/${module.id}`}
      aria-label={ariaLabel}
      className={cn(
        baseClasses,
        'bg-card border-border hover:shadow-brand-md hover:border-border-strong motion-safe:hover:-translate-y-0.5'
      )}
    >
      {content}
    </Link>
  )
}
