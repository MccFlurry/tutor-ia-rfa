import {
  Rocket,
  Trophy,
  Flame,
  Bot,
  Star,
  GraduationCap,
  Zap,
  Award,
  type LucideIcon,
} from 'lucide-react'
import type { Achievement, AchievementConditionType } from '@/types/achievement'

const ICON_MAP: Record<AchievementConditionType, LucideIcon> = {
  first_topic:      Rocket,
  module_completed: Trophy,
  streak_days:      Flame,
  chat_messages:    Bot,
  quiz_perfect:     Star,
  course_completed: GraduationCap,
}

export function getAchievementIcon(achievement: Pick<Achievement, 'condition_type' | 'condition_module_id'>): LucideIcon {
  // Module-specific completions (e.g. Maestro Kotlin) get distinct icon
  if (achievement.condition_type === 'module_completed' && achievement.condition_module_id != null) {
    return Zap
  }
  return ICON_MAP[achievement.condition_type as AchievementConditionType] ?? Award
}
