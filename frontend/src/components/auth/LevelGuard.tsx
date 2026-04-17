import { Navigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { usersApi } from '@/api/users'
import { useAuthStore } from '@/store/authStore'

interface LevelGuardProps {
  children: React.ReactNode
}

export default function LevelGuard({ children }: LevelGuardProps) {
  const location = useLocation()
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === 'admin'

  const { data, isLoading } = useQuery({
    queryKey: ['my-level'],
    queryFn: () => usersApi.getLevel().then((r) => r.data),
    staleTime: 60_000,
    enabled: !isAdmin, // admins skip assessment
  })

  // Admins bypass entry assessment entirely
  if (isAdmin) return <>{children}</>

  if (isLoading) {
    return (
      <div className="min-h-dvh flex items-center justify-center bg-gray-50">
        <div className="text-gray-500 text-sm">Cargando tu perfil...</div>
      </div>
    )
  }

  if (!data?.level) {
    return <Navigate to="/assessment" state={{ from: location }} replace />
  }

  return <>{children}</>
}
