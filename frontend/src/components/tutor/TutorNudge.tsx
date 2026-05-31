import { Link } from 'react-router-dom'
import { Compass, Rocket, Hand, Flag, Flame, Repeat, Sparkles, Trophy, CheckCircle2 } from 'lucide-react'
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

export default function TutorNudge({ nudge }: { nudge: Nudge }) {
  const Icon = ICONS[nudge.icon] ?? Sparkles
  return (
    <div
      className={`flex gap-3 rounded-lg border p-4 ${TONE[nudge.tone]}`}
      role="status"
    >
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
    </div>
  )
}
