import toast from 'react-hot-toast'
import type { QueryClient } from '@tanstack/react-query'
import type { LevelChange } from '@/types/quiz'

const LABEL: Record<LevelChange['new_level'], string> = {
  beginner: 'Principiante',
  intermediate: 'Intermedio',
  advanced: 'Avanzado',
}

/**
 * React to a server-applied level change: show a toast and refresh any cache
 * key that depends on the user's level (level badge, dashboard, modal).
 */
export function handleLevelChange(
  change: LevelChange | null | undefined,
  queryClient: QueryClient,
): void {
  if (!change) return

  const icon = change.direction === 'up' ? '🎉' : '📚'
  const verb = change.direction === 'up' ? 'subiste' : 'bajaste'
  toast.success(
    `${icon} ¡${verb} a nivel ${LABEL[change.new_level]}! ${change.reason}`,
    { duration: 6000 },
  )

  queryClient.invalidateQueries({ queryKey: ['my-level'] })
  queryClient.invalidateQueries({ queryKey: ['reassessment-proposal'] })
  queryClient.invalidateQueries({ queryKey: ['dashboard'] })
}
