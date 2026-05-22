import * as React from 'react'
import { cn } from '@/lib/utils'

interface PageHeaderProps {
  title: string
  subtitle?: React.ReactNode
  eyebrow?: React.ReactNode
  actions?: React.ReactNode
  className?: string
}

export default function PageHeader({
  title,
  subtitle,
  eyebrow,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <header className={cn('mb-8 flex items-start justify-between flex-wrap gap-4', className)}>
      <div className="min-w-0">
        {eyebrow ? (
          <div className="mb-3">{eyebrow}</div>
        ) : (
          <span className="heritage-accent-bar mb-3" aria-hidden="true" />
        )}
        <h1 className="text-2xl sm:text-3xl font-extrabold text-institutional-700 dark:text-institutional-100 mb-1">
          {title}
        </h1>
        {subtitle && (
          <p className="text-muted-foreground text-sm sm:text-base">{subtitle}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </header>
  )
}
