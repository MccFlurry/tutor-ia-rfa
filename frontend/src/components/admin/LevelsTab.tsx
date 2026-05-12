import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { adminApi } from '@/api/admin'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { StudentLevel } from '@/types/assessment'

const LEVEL_COLOR: Record<string, string> = {
  beginner: 'bg-muted text-muted-foreground',
  intermediate: 'bg-info/10 text-info',
  advanced: 'bg-primary/10 text-primary',
}

export default function LevelsTab() {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['admin', 'user-levels'],
    queryFn: () => adminApi.listUserLevels().then((r) => r.data),
  })

  const override = useMutation({
    mutationFn: ({ id, level, reason }: { id: string; level: StudentLevel; reason: string }) =>
      adminApi.overrideUserLevel(id, level, reason),
    onSuccess: () => {
      toast.success('Nivel actualizado')
      queryClient.invalidateQueries({ queryKey: ['admin', 'user-levels'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
    },
    onError: () => toast.error('Error al sobreescribir'),
  })

  const handleOverride = (userId: string, userName: string) => {
    const level = prompt(
      `Nuevo nivel para ${userName} (beginner/intermediate/advanced):`,
      'intermediate'
    ) as StudentLevel
    if (!['beginner', 'intermediate', 'advanced'].includes(level)) {
      return toast.error('Nivel inválido')
    }
    const reason = prompt('Razón del override (registro en historial):')
    if (!reason) return
    override.mutate({ id: userId, level, reason })
  }

  return (
    <div>
      <h3 className="font-semibold text-foreground mb-1">Niveles de estudiantes</h3>
      <p className="text-sm text-muted-foreground mb-4">
        Nivel asignado por evaluación de entrada o re-asignación automática. Puedes sobrescribir manualmente.
      </p>

      <div className="bg-card border border-border rounded-xl overflow-x-auto">
        {isLoading ? (
          <div className="p-8 text-center text-muted-foreground">Cargando...</div>
        ) : !data || data.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground text-sm">Sin estudiantes</div>
        ) : (
          <table className="w-full text-sm min-w-[720px]">
            <thead className="bg-muted text-muted-foreground text-xs uppercase">
              <tr>
                <th className="px-4 py-3 text-left">Estudiante</th>
                <th className="px-4 py-3 text-left">Email</th>
                <th className="px-4 py-3 text-left">Nivel</th>
                <th className="px-4 py-3 text-right">Score</th>
                <th className="px-4 py-3 text-left">Evaluado</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <tr key={row.user_id} className="border-t border-border">
                  <td className="px-4 py-3 font-medium text-foreground">{row.full_name}</td>
                  <td className="px-4 py-3 text-muted-foreground">{row.email}</td>
                  <td className="px-4 py-3">
                    {row.level ? (
                      <span
                        className={cn(
                          'text-xs font-semibold px-2 py-0.5 rounded',
                          LEVEL_COLOR[row.level]
                        )}
                      >
                        {row.level}
                      </span>
                    ) : (
                      <span className="text-xs italic text-muted-foreground">sin evaluar</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right text-foreground">
                    {row.entry_score !== null ? row.entry_score.toFixed(1) : '—'}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {row.assessed_at
                      ? new Date(row.assessed_at).toLocaleDateString('es-PE')
                      : '—'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleOverride(row.user_id, row.full_name)}
                    >
                      Override
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
