import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ShieldCheck, ShieldOff } from 'lucide-react'
import toast from 'react-hot-toast'
import { adminApi } from '@/api/admin'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import ConfirmDialog from '@/components/common/ConfirmDialog'

interface RoleDlg {
  open: boolean
  userId: string | null
  userName: string
  newRole: string
}

export default function UsersTab() {
  const queryClient = useQueryClient()
  const [roleDlg, setRoleDlg] = useState<RoleDlg>({
    open: false,
    userId: null,
    userName: '',
    newRole: '',
  })

  const { data: users, isLoading } = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => adminApi.listUsers().then((r) => r.data),
  })

  const update = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => adminApi.updateUser(id, data),
    onSuccess: () => {
      toast.success('Usuario actualizado')
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Error'),
  })

  // Any role change (both directions) goes through a confirmation.
  const handleRoleChange = (userId: string, userName: string, newRole: string) => {
    setRoleDlg({ open: true, userId, userName, newRole })
  }

  const handleConfirmRole = () => {
    if (!roleDlg.userId) return
    update.mutate(
      { id: roleDlg.userId, data: { role: roleDlg.newRole } },
      { onSettled: () => setRoleDlg({ open: false, userId: null, userName: '', newRole: '' }) }
    )
  }

  const promoting = roleDlg.newRole === 'admin'

  return (
    <div>
      <h3 className="font-semibold text-foreground mb-4">Usuarios del sistema</h3>
      <div className="bg-card border border-border rounded-xl overflow-x-auto">
        {isLoading ? (
          <div className="p-6 space-y-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-10 bg-muted animate-pulse rounded" />
            ))}
          </div>
        ) : !users || users.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground text-sm">Sin usuarios</div>
        ) : (
          <table className="w-full text-sm min-w-[640px]">
            <thead className="bg-muted text-muted-foreground text-xs uppercase">
              <tr>
                <th scope="col" className="px-4 py-3 text-left">Nombre</th>
                <th scope="col" className="px-4 py-3 text-left">Email</th>
                <th scope="col" className="px-4 py-3 text-left">Rol</th>
                <th scope="col" className="px-4 py-3 text-left">Nivel</th>
                <th scope="col" className="px-4 py-3 text-left">Estado</th>
                <th scope="col" className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-border">
                  <td className="px-4 py-3 font-medium text-foreground">{u.full_name}</td>
                  <td className="px-4 py-3 text-muted-foreground">{u.email}</td>
                  <td className="px-4 py-3">
                    <select
                      value={u.role}
                      onChange={(e) => handleRoleChange(u.id, u.full_name, e.target.value)}
                      className="text-xs border border-border bg-background text-foreground rounded px-2 py-1"
                    >
                      <option value="student">student</option>
                      <option value="admin">admin</option>
                    </select>
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {u.level || <span className="italic text-muted-foreground">sin evaluar</span>}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        'text-xs font-semibold px-2 py-0.5 rounded',
                        u.is_active ? 'bg-success/10 text-success' : 'bg-muted text-muted-foreground'
                      )}
                    >
                      {u.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      size="sm"
                      variant="ghost"
                      aria-label={u.is_active ? 'Desactivar usuario' : 'Activar usuario'}
                      onClick={() =>
                        update.mutate({ id: u.id, data: { is_active: !u.is_active } })
                      }
                    >
                      {u.is_active ? (
                        <ShieldOff className="w-3 h-3 text-destructive" />
                      ) : (
                        <ShieldCheck className="w-3 h-3 text-success" />
                      )}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <ConfirmDialog
        open={roleDlg.open}
        onOpenChange={(o) => setRoleDlg((s) => ({ ...s, open: o }))}
        title={
          promoting
            ? `¿Promover a "${roleDlg.userName}" como administrador?`
            : `¿Quitar el rol de administrador a "${roleDlg.userName}"?`
        }
        description={
          promoting
            ? 'Este usuario tendrá acceso completo al panel de administración: corpus RAG, contenido, usuarios, banco de preguntas y niveles.'
            : 'Volverá a ser estudiante y perderá el acceso al panel de administración.'
        }
        confirmLabel={promoting ? 'Sí, promover' : 'Sí, quitar acceso'}
        destructive={!promoting}
        pending={update.isPending}
        onConfirm={handleConfirmRole}
      />
    </div>
  )
}
