import { Menu, LogOut } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useLogout } from '@/hooks/useAuth'
import LevelBadge from './LevelBadge'

interface NavbarProps {
  onMenuClick: () => void
}

function initials(fullName?: string) {
  if (!fullName) return '??'
  const parts = fullName.trim().split(/\s+/)
  return (parts[0]?.[0] ?? '') + (parts[1]?.[0] ?? '')
}

export default function Navbar({ onMenuClick }: NavbarProps) {
  const user = useAuthStore((s) => s.user)
  const logout = useLogout()

  return (
    <header
      role="banner"
      className="bg-white/95 backdrop-blur border-b border-gray-200 px-4 py-3 flex items-center justify-between lg:px-6 sticky top-0 z-30"
    >
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onMenuClick}
          aria-label="Abrir menú"
          className="lg:hidden text-gray-500 hover:text-gray-800 p-2 -ml-2 rounded-lg"
        >
          <Menu className="w-6 h-6" />
        </button>

        <div className="hidden lg:flex flex-col leading-tight">
          <span className="text-xs font-semibold uppercase tracking-wider text-heritage-600">
            IESTP RFA · Chiclayo
          </span>
          <h1 className="text-base font-bold text-institutional-700">
            Sistema de Tutoría Inteligente
          </h1>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <LevelBadge />

        {user && (
          <div className="flex items-center gap-2">
            <div
              aria-hidden="true"
              className="w-9 h-9 rounded-full bg-institutional-700 text-white flex items-center justify-center text-xs font-bold shadow-brand-sm"
            >
              {initials(user.full_name).toUpperCase()}
            </div>
            <div className="text-right hidden sm:block min-w-0">
              <p className="text-sm font-semibold text-gray-900 truncate max-w-[160px]">
                {user.full_name}
              </p>
              <p className="text-xs text-gray-500 capitalize">
                {user.role === 'admin' ? 'Administrador' : 'Estudiante'}
              </p>
            </div>
          </div>
        )}

        <button
          onClick={logout}
          aria-label="Cerrar sesión"
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-peru-600 transition p-2 rounded-lg min-h-[44px] min-w-[44px] justify-center"
          title="Cerrar sesión"
        >
          <LogOut className="w-4 h-4" />
          <span className="hidden sm:inline">Salir</span>
        </button>
      </div>
    </header>
  )
}
