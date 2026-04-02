import { Menu, LogOut } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useLogout } from '@/hooks/useAuth'

interface NavbarProps {
  onMenuClick: () => void
}

export default function Navbar({ onMenuClick }: NavbarProps) {
  const user = useAuthStore((s) => s.user)
  const logout = useLogout()

  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between lg:px-6">
      <button
        onClick={onMenuClick}
        className="lg:hidden text-gray-500 hover:text-gray-700"
      >
        <Menu className="w-6 h-6" />
      </button>

      <h1 className="text-lg font-bold text-gray-900 hidden lg:block">
        Sistema de Tutoría Inteligente
      </h1>

      <div className="flex items-center gap-4">
        <div className="text-right hidden sm:block">
          <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
          <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-red-600 transition"
          title="Cerrar sesión"
        >
          <LogOut className="w-4 h-4" />
          <span className="hidden sm:inline">Salir</span>
        </button>
      </div>
    </header>
  )
}
