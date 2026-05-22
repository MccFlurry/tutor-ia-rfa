import { Menu, LogOut } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useLogout } from '@/hooks/useAuth'
import LevelBadge from './LevelBadge'
import ThemeToggle from './ThemeToggle'
import Avatar from '@/components/common/Avatar'

interface NavbarProps {
  onMenuClick: () => void
}

export default function Navbar({ onMenuClick }: NavbarProps) {
  const user = useAuthStore((s) => s.user)
  const logout = useLogout()

  return (
    <header
      role="banner"
      className="bg-background/95 backdrop-blur border-b border-border px-4 py-3 flex items-center justify-between lg:px-6 sticky top-0 z-30"
    >
      <div className="flex items-center gap-3 min-w-0">
        <button
          type="button"
          onClick={onMenuClick}
          aria-label="Abrir menú"
          aria-haspopup="dialog"
          className="lg:hidden inline-flex items-center justify-center min-h-[44px] min-w-[44px] -ml-2
                     text-muted-foreground hover:text-foreground rounded-lg
                     focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
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

      <div className="flex items-center gap-2 sm:gap-3">
        <ThemeToggle />
        <LevelBadge />

        {user && (
          <div className="flex items-center gap-2">
            <Avatar fullName={user.full_name} src={user.avatar_url} size="md" />
            <div className="text-right hidden sm:block min-w-0">
              <p className="text-sm font-semibold text-foreground truncate max-w-[160px]">
                {user.full_name}
              </p>
              <p className="text-xs text-muted-foreground capitalize">
                {user.role === 'admin' ? 'Administrador' : 'Estudiante'}
              </p>
            </div>
          </div>
        )}

        <button
          onClick={logout}
          aria-label="Cerrar sesión"
          className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-peru-600 transition p-2 rounded-lg min-h-[44px] min-w-[44px] justify-center"
          title="Cerrar sesión"
        >
          <LogOut className="w-4 h-4" />
          <span className="hidden sm:inline">Salir</span>
        </button>
      </div>
    </header>
  )
}
