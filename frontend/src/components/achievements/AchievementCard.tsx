import { Lock } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Achievement } from '@/types/achievement'

interface AchievementCardProps {
  achievement: Achievement
}

export default function AchievementCard({ achievement }: AchievementCardProps) {
  const earned = achievement.is_earned

  return (
    <div
      className={cn(
        'rounded-xl border p-4 text-center transition',
        earned
          ? 'bg-white border-gray-200'
          : 'bg-gray-50 border-gray-100 opacity-60 grayscale'
      )}
    >
      <div className="text-3xl mb-2">
        {earned ? achievement.badge_emoji : <Lock className="w-7 h-7 mx-auto text-gray-300" />}
      </div>
      <p className="font-semibold text-sm text-gray-900 mb-0.5">{achievement.name}</p>
      <p className="text-xs text-gray-500 leading-relaxed">{achievement.description}</p>
      {earned && achievement.earned_at && (
        <p className="text-xs text-gray-400 mt-2">
          {new Date(achievement.earned_at).toLocaleDateString('es-PE')}
        </p>
      )}
    </div>
  )
}
