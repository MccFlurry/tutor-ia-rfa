import { useQuery } from '@tanstack/react-query'
import { TrendingUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { usersApi } from '@/api/users'
import { useAuthStore } from '@/store/authStore'
import type { StudentLevel } from '@/types/assessment'

const LABELS: Record<StudentLevel, string> = {
  beginner: 'Principiante',
  intermediate: 'Intermedio',
  advanced: 'Avanzado',
}

const STYLES: Record<StudentLevel, string> = {
  beginner:     'bg-muted text-muted-foreground',
  intermediate: 'bg-primary/10 text-primary',
  advanced:     'bg-heritage-100 text-heritage-700 dark:bg-heritage-700/20 dark:text-heritage-400',
}

export default function LevelBadge() {
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === 'admin'

  const { data } = useQuery({
    queryKey: ['my-level'],
    queryFn: () => usersApi.getLevel().then((r) => r.data),
    staleTime: 60_000,
    enabled: !isAdmin,
  })

  if (isAdmin || !data?.level) return null

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full',
        STYLES[data.level]
      )}
      title={`Tu nivel actual: ${LABELS[data.level]}`}
    >
      <TrendingUp className="w-3 h-3" />
      {LABELS[data.level]}
    </span>
  )
}
