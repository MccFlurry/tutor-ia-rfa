import { Link } from 'react-router-dom'
import { Repeat, Target } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ModuleDiagnostic } from '@/types/companion'

interface Props {
  diagnostic: ModuleDiagnostic
  className?: string
}

const CHIP_BASE =
  'inline-flex items-center gap-1.5 min-h-[44px] px-3.5 rounded-full border text-sm font-medium ' +
  'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'

export default function DiagnosticChips({ diagnostic, className }: Props) {
  const { weak, practice } = diagnostic
  if (weak.length === 0 && practice.length === 0) return null
  return (
    <ul aria-label="Diagnóstico de temas del módulo" className={cn('flex flex-wrap gap-2', className)}>
      {weak.map((t) => (
        <li key={`weak-${t.topic_id}`}>
          <Link
            to={`/topics/${t.topic_id}`}
            className={cn(CHIP_BASE, 'bg-warning/10 text-warning border-warning/30 hover:bg-warning/20')}
          >
            <Repeat className="w-3.5 h-3.5" aria-hidden="true" />
            Repasar: {t.title}
          </Link>
        </li>
      ))}
      {practice.map((t) => (
        <li key={`practice-${t.topic_id}`}>
          <Link
            to={`/topics/${t.topic_id}`}
            className={cn(CHIP_BASE, 'bg-primary/10 text-primary border-primary/30 hover:bg-primary/20')}
          >
            <Target className="w-3.5 h-3.5" aria-hidden="true" />
            Afianzar: {t.title}
          </Link>
        </li>
      ))}
    </ul>
  )
}
