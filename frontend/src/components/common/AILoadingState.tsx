import { Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AILoadingStateProps {
  title?: string
  subtitle?: string
  className?: string
}

export default function AILoadingState({
  title = 'La IA está trabajando...',
  subtitle = 'Esto puede tomar unos segundos.',
  className,
}: AILoadingStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-16 text-center',
        className
      )}
      role="status"
      aria-live="polite"
    >
      <div
        className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-6 animate-pulse"
        aria-hidden="true"
      >
        <Sparkles className="w-8 h-8 text-primary-600" />
      </div>
      <h2 className="text-xl font-bold text-foreground mb-2">{title}</h2>
      <p className="text-sm text-muted-foreground max-w-md">{subtitle}</p>
      <div className="mt-6 flex gap-1" aria-hidden="true">
        <span
          className="w-2 h-2 bg-primary-400 rounded-full animate-bounce"
          style={{ animationDelay: '0ms' }}
        />
        <span
          className="w-2 h-2 bg-primary-400 rounded-full animate-bounce"
          style={{ animationDelay: '150ms' }}
        />
        <span
          className="w-2 h-2 bg-primary-400 rounded-full animate-bounce"
          style={{ animationDelay: '300ms' }}
        />
      </div>
    </div>
  )
}
