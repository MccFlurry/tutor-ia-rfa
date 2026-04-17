import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { usersApi } from '@/api/users'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { StudentLevel } from '@/types/assessment'

const LABEL: Record<StudentLevel, string> = {
  beginner: 'Principiante',
  intermediate: 'Intermedio',
  advanced: 'Avanzado',
}

const DISMISS_KEY = 'reassess_dismissed_at'

export default function ReassessmentModal() {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === 'admin'

  const { data } = useQuery({
    queryKey: ['reassessment-proposal'],
    queryFn: () => usersApi.getReassessmentProposal().then((r) => r.data),
    staleTime: 30_000,
    refetchInterval: 60_000,
    enabled: !isAdmin,
  })

  useEffect(() => {
    if (!data?.should_reassess) {
      setOpen(false)
      return
    }
    // Don't reopen if user dismissed in the last hour
    const dismissedAt = localStorage.getItem(DISMISS_KEY)
    if (dismissedAt) {
      const diff = Date.now() - Number(dismissedAt)
      if (diff < 60 * 60 * 1000) return
    }
    setOpen(true)
  }, [data])

  const confirmMutation = useMutation({
    mutationFn: (accept: boolean) => usersApi.confirmReassessment(accept),
    onSuccess: (_, accept) => {
      if (accept) {
        toast.success('¡Nivel actualizado!')
      }
      queryClient.invalidateQueries({ queryKey: ['my-level'] })
      queryClient.invalidateQueries({ queryKey: ['reassessment-proposal'] })
      setOpen(false)
    },
    onError: () => toast.error('No se pudo actualizar el nivel'),
  })

  const handleDismiss = () => {
    localStorage.setItem(DISMISS_KEY, String(Date.now()))
    setOpen(false)
  }

  if (!open || !data?.should_reassess) return null

  const isUp = data.direction === 'up'
  const Icon = isUp ? TrendingUp : TrendingDown
  const title = isUp
    ? '¡Lo estás haciendo excelente!'
    : 'Ajustemos tu nivel'
  const description = isUp
    ? `Tus últimos desempeños muestran que dominas el nivel ${LABEL[data.current_level!]}. ¿Quieres subir a ${LABEL[data.proposed_level!]}?`
    : `Notamos que el nivel ${LABEL[data.current_level!]} está siendo exigente. ¿Quieres bajar a ${LABEL[data.proposed_level!]} para consolidar conceptos?`

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6 relative">
        <button
          onClick={handleDismiss}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
        >
          <X className="w-5 h-5" />
        </button>

        <div
          className={cn(
            'w-14 h-14 rounded-full flex items-center justify-center mb-4',
            isUp ? 'bg-green-100' : 'bg-yellow-100'
          )}
        >
          <Icon
            className={cn('w-7 h-7', isUp ? 'text-green-600' : 'text-yellow-600')}
          />
        </div>

        <h3 className="text-lg font-bold text-gray-900 mb-2">{title}</h3>
        <p className="text-gray-600 text-sm mb-2">{description}</p>
        <p className="text-xs text-gray-400 mb-6">{data.reason}</p>

        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => confirmMutation.mutate(false)}
            disabled={confirmMutation.isPending}
            className="flex-1"
          >
            Ahora no
          </Button>
          <Button
            onClick={() => confirmMutation.mutate(true)}
            disabled={confirmMutation.isPending}
            className="flex-1"
          >
            {isUp ? 'Subir nivel' : 'Bajar nivel'}
          </Button>
        </div>
      </div>
    </div>
  )
}
