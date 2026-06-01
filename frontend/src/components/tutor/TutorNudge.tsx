import { Link } from 'react-router-dom'
import { Compass, Rocket, Hand, Flag, Flame, Repeat, Sparkles, Trophy, CheckCircle2, X } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { Nudge, NudgeTone } from '@/types/tutor'

const ICONS: Record<string, LucideIcon> = {
  compass: Compass, rocket: Rocket, hand: Hand,
  flag: Flag, flame: Flame, repeat: Repeat,
  trophy: Trophy, check: CheckCircle2,
}

// Clases por tono usando tokens semánticos (dark-mode safe)
const TONE: Record<NudgeTone, string> = {
  info: 'border-primary/30 bg-primary/5',
  success: 'border-green-500/30 bg-green-500/5',
  warning: 'border-amber-500/30 bg-amber-500/5',
  encourage: 'border-primary/30 bg-primary/5',
}

interface TutorNudgeProps {
  nudge: Nudge
  onDismiss?: (id: string) => void
}

export default function TutorNudge({ nudge, onDismiss }: TutorNudgeProps) {
  const Icon = ICONS[nudge.icon] ?? Sparkles
  return (
    <div className={`flex gap-3 rounded-lg border p-4 ${TONE[nudge.tone]}`}>
      <Icon className="h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
      <div className="flex-1 space-y-1">
        <p className="font-semibold text-foreground">{nudge.title}</p>
        <p className="text-sm text-muted-foreground">{nudge.message}</p>
        {nudge.cta_route && nudge.cta_label && (
          <Link
            to={nudge.cta_route}
            className="inline-flex min-h-[44px] items-center text-sm font-medium text-primary hover:underline"
          >
            {nudge.cta_label}
          </Link>
        )}
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={() => onDismiss(String(nudge.id))}
          aria-label="Descartar mensaje"
          className="-m-1 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg
                     text-muted-foreground hover:text-foreground hover:bg-foreground/5
                     focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      )}
    </div>
  )
}
