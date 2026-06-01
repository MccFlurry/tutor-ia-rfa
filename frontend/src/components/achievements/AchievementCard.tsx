import { Lock } from 'lucide-react'
import { cn } from '@/lib/utils'
import { getAchievementIcon } from '@/lib/achievementIcon'
import type { Achievement } from '@/types/achievement'

interface AchievementCardProps {
  achievement: Achievement
}

export default function AchievementCard({ achievement }: AchievementCardProps) {
  const earned = achievement.is_earned
  const Icon = getAchievementIcon(achievement)

  return (
    <div
      aria-label={earned ? undefined : `${achievement.name} — bloqueado`}
      style={earned ? ({ '--badge-color': achievement.badge_color } as React.CSSProperties) : undefined}
      className={cn(
        'rounded-xl border p-4 text-center transition',
        earned
          ? 'bg-card border-[color:var(--badge-color)]/30 shadow-brand-sm'
          : 'bg-muted/50 border-border'
      )}
    >
      <div
        className={cn(
          'w-12 h-12 mx-auto mb-2 rounded-full flex items-center justify-center',
          earned ? 'bg-[color:var(--badge-color)]/15' : 'bg-muted'
        )}
        aria-hidden="true"
      >
        {earned ? (
          <Icon
            className="w-6 h-6"
            style={{ color: achievement.badge_color }}
            strokeWidth={2}
          />
        ) : (
          <Lock className="w-6 h-6 text-muted-foreground" />
        )}
      </div>
      <p className="font-semibold text-sm text-foreground mb-0.5">{achievement.name}</p>
      <p className="text-xs text-muted-foreground leading-relaxed">{achievement.description}</p>
      {earned && achievement.earned_at && (
        <p className="text-xs text-muted-foreground/70 mt-2">
          {new Date(achievement.earned_at).toLocaleDateString('es-PE')}
        </p>
      )}
      {!earned && (
        <p className="text-[11px] font-medium text-muted-foreground mt-2">Bloqueado</p>
      )}
    </div>
  )
}
