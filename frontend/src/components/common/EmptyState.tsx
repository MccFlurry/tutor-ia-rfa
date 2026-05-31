import * as React from 'react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

type EmptyStateTone = 'default' | 'error'

const TONE_CIRCLE: Record<EmptyStateTone, string> = {
  default: 'bg-primary-50 dark:bg-primary/15',
  error: 'bg-destructive/10',
}

const TONE_ICON: Record<EmptyStateTone, string> = {
  default: 'text-primary-500',
  error: 'text-destructive',
}

interface EmptyStateProps {
  icon?: LucideIcon
  illustration?: string | React.ReactNode
  illustrationAlt?: string
  title: string
  description?: React.ReactNode
  action?: React.ReactNode
  /** Visual tone of the icon badge: neutral 'default' or a 'error' (destructive) treatment. */
  tone?: EmptyStateTone
  className?: string
}

export default function EmptyState({
  icon: Icon,
  illustration,
  illustrationAlt,
  title,
  description,
  action,
  tone = 'default',
  className,
}: EmptyStateProps) {
  const showIllustration = !!illustration
  const showIcon = !showIllustration && !!Icon

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 px-4 text-center',
        className
      )}
    >
      {showIllustration && (
        <div className="mb-6 max-w-[280px] w-full">
          {typeof illustration === 'string' ? (
            <img
              src={illustration}
              alt={illustrationAlt ?? ''}
              className="w-full h-auto select-none"
              loading="lazy"
              draggable={false}
            />
          ) : (
            illustration
          )}
        </div>
      )}
      {showIcon && Icon && (
        <div
          className={cn(
            'w-14 h-14 rounded-full flex items-center justify-center mb-4',
            TONE_CIRCLE[tone]
          )}
          aria-hidden="true"
        >
          <Icon className={cn('w-7 h-7', TONE_ICON[tone])} />
        </div>
      )}
      <h3 className="text-base font-semibold text-foreground mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground max-w-md mb-4">{description}</p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}
