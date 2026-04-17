import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ShieldCheck, ShieldOff } from 'lucide-react'
import toast from 'react-hot-toast'
import { adminApi } from '@/api/admin'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export default function UsersTab() {
  const queryClient = useQueryClient()

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

  return (
    <div>
      <h3 className="font-semibold text-gray-900 mb-4">Usuarios del sistema</h3>
      <div className="bg-white border border-gray-200 rounded-xl overflow-x-auto">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Cargando...</div>
        ) : !users || users.length === 0 ? (
          <div className="p-8 text-center text-gray-500 text-sm">Sin usuarios</div>
        ) : (
          <table className="w-full text-sm min-w-[640px]">
            <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
              <tr>
                <th className="px-4 py-3 text-left">Nombre</th>
                <th className="px-4 py-3 text-left">Email</th>
                <th className="px-4 py-3 text-left">Rol</th>
                <th className="px-4 py-3 text-left">Nivel</th>
                <th className="px-4 py-3 text-left">Estado</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-gray-100">
                  <td className="px-4 py-3 font-medium text-gray-800">{u.full_name}</td>
                  <td className="px-4 py-3 text-gray-600">{u.email}</td>
                  <td className="px-4 py-3">
                    <select
                      value={u.role}
                      onChange={(e) =>
                        update.mutate({ id: u.id, data: { role: e.target.value } })
                      }
                      className="text-xs border border-gray-200 rounded px-2 py-1"
                    >
                      <option value="student">student</option>
                      <option value="admin">admin</option>
                    </select>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-600">
                    {u.level || <span className="italic text-gray-400">sin evaluar</span>}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        'text-xs font-semibold px-2 py-0.5 rounded',
                        u.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                      )}
                    >
                      {u.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() =>
                        update.mutate({ id: u.id, data: { is_active: !u.is_active } })
                      }
                    >
                      {u.is_active ? (
                        <ShieldOff className="w-3 h-3 text-red-500" />
                      ) : (
                        <ShieldCheck className="w-3 h-3 text-green-500" />
                      )}
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
