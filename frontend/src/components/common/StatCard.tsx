import * as React from 'react'
import { cn } from '@/lib/utils'
import { Progress } from '@/components/ui/progress'

type Accent = 'primary' | 'success' | 'warning' | 'heritage' | 'info' | 'neutral'

interface StatCardProps {
  label: string
  value: React.ReactNode
  icon?: React.ComponentType<{ className?: string }>
  accent?: Accent
  progress?: number
  helperText?: React.ReactNode
  className?: string
}

const ACCENT_ICON_BG: Record<Accent, string> = {
  primary:   'bg-primary-100 text-primary-600',
  success:   'bg-green-100 text-green-600',
  warning:   'bg-amber-100 text-amber-600',
  heritage:  'bg-heritage-100 text-heritage-700',
  info:      'bg-sky-100 text-sky-600',
  neutral:   'bg-muted text-muted-foreground',
}

const ACCENT_VALUE_COLOR: Record<Accent, string> = {
  primary:   'text-primary-700',
  success:   'text-green-700',
  warning:   'text-amber-700',
  heritage:  'text-heritage-700',
  info:      'text-sky-700',
  neutral:   'text-foreground',
}

export default function StatCard({
  label,
  value,
  icon: Icon,
  accent = 'neutral',
  progress,
  helperText,
  className,
}: StatCardProps) {
  return (
    <article
      className={cn(
        'bg-card rounded-xl border border-border shadow-brand-sm p-5',
        className
      )}
    >
      <div className="flex items-center gap-3 mb-2">
        {Icon && (
          <div
            className={cn(
              'w-9 h-9 rounded-lg flex items-center justify-center shrink-0',
              ACCENT_ICON_BG[accent]
            )}
            aria-hidden="true"
          >
            <Icon className="w-5 h-5" />
          </div>
        )}
        <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">
          {label}
        </p>
      </div>
      <p className={cn('text-3xl font-extrabold tabular-nums mt-1', ACCENT_VALUE_COLOR[accent])}>
        {value}
      </p>
      {progress !== undefined && (
        <Progress value={progress} className="h-2 mt-3" />
      )}
      {helperText && (
        <p className="text-xs text-muted-foreground mt-2">{helperText}</p>
      )}
    </article>
  )
}
