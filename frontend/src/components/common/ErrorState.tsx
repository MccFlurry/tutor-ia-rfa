import * as React from 'react'
import { AlertTriangle, ServerCrash, FileQuestion } from 'lucide-react'
import { cn } from '@/lib/utils'

type ErrorVariant = 'generic' | 'serviceUnavailable' | 'notFound'

const VARIANT_ICON = {
  generic: AlertTriangle,
  serviceUnavailable: ServerCrash,
  notFound: FileQuestion,
}

interface ErrorStateProps {
  variant?: ErrorVariant
  title: string
  description?: React.ReactNode
  action?: React.ReactNode
  className?: string
}

export default function ErrorState({
  variant = 'generic',
  title,
  description,
  action,
  className,
}: ErrorStateProps) {
  const Icon = VARIANT_ICON[variant]
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-16 px-4 text-center',
        className
      )}
      role="alert"
    >
      <div
        className="w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center mb-4"
        aria-hidden="true"
      >
        <Icon className="w-8 h-8 text-destructive" />
      </div>
      <h2 className="text-lg font-bold text-foreground mb-2">{title}</h2>
      {description && (
        <p className="text-sm text-muted-foreground max-w-md mb-6">{description}</p>
      )}
      {action && <div className="flex flex-wrap gap-3 justify-center">{action}</div>}
    </div>
  )
}
