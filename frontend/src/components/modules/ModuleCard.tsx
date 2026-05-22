import { useNavigate } from 'react-router-dom'
import { Lock } from 'lucide-react'
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

function getStatusBadge(module: Module) {
  if (module.is_locked) return { label: 'Bloqueado', variant: 'secondary' as const }
  if (module.progress_pct >= 100) return { label: 'Completado', variant: 'default' as const }
  if (module.progress_pct > 0) return { label: 'En progreso', variant: 'outline' as const }
  return { label: 'No iniciado', variant: 'secondary' as const }
}

const LOCKED_REASON = 'Completa el módulo anterior para desbloquear este contenido.'

export default function ModuleCard({ module }: ModuleCardProps) {
  const navigate = useNavigate()
  const Icon = getIcon(module.icon_name)
  const status = getStatusBadge(module)
  const locked = module.is_locked

  const handleClick = () => {
    if (!locked) {
      navigate(`/modules/${module.id}`)
    }
  }

  const ariaLabel = locked
    ? `${module.title} — Bloqueado. ${LOCKED_REASON}`
    : `${module.title} — ${Math.round(module.progress_pct)}% completado`

  return (
    <article
      role={locked ? undefined : 'button'}
      tabIndex={locked ? -1 : 0}
      onClick={handleClick}
      onKeyDown={(e) => {
        if (!locked && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault()
          handleClick()
        }
      }}
      aria-label={ariaLabel}
      aria-disabled={locked || undefined}
      title={locked ? LOCKED_REASON : undefined}
      className={cn(
        'relative bg-card rounded-xl border border-border p-6 transition-all',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        locked
          ? 'opacity-70 cursor-not-allowed select-none'
          : 'cursor-pointer hover:shadow-brand-md hover:border-border-strong motion-safe:hover:-translate-y-0.5'
      )}
      style={!locked ? ({ '--module-color': module.color_hex } as React.CSSProperties) : undefined}
    >
      {/* Icon + Badge row */}
      <div className="flex items-start justify-between mb-4">
        <div
          className={cn(
            'w-12 h-12 rounded-lg flex items-center justify-center',
            locked && 'bg-muted'
          )}
          style={
            !locked
              ? { backgroundColor: `${module.color_hex}20` }
              : undefined
          }
          aria-hidden="true"
        >
          {locked ? (
            <Lock className="w-6 h-6 text-muted-foreground" />
          ) : (
            <Icon className="w-6 h-6" style={{ color: module.color_hex }} />
          )}
        </div>
        <Badge variant={status.variant}>{status.label}</Badge>
      </div>

      {/* Title + Description */}
      <h3 className="font-semibold text-foreground mb-1 line-clamp-2">
        {module.title}
      </h3>
      <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
        {module.description}
      </p>

      {/* Locked reason banner */}
      {locked && (
        <div
          className="flex items-start gap-2 mb-4 text-xs text-muted-foreground bg-muted/50 rounded-lg p-2.5"
          role="note"
        >
          <Lock className="w-3.5 h-3.5 shrink-0 mt-0.5" aria-hidden="true" />
          <span>{LOCKED_REASON}</span>
        </div>
      )}

      {/* Progress */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-muted-foreground tabular-nums">
          <span>
            {module.completed_topics} de {module.total_topics} temas
          </span>
          <span>{Math.round(module.progress_pct)}%</span>
        </div>
        <Progress value={module.progress_pct} className="h-2" />
      </div>
    </article>
  )
}
