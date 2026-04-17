import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  BookOpen,
  MessageCircle,
  BarChart3,
  Trophy,
  Settings,
  X,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import BrandLogo from '@/components/brand/BrandLogo'

const studentLinks = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Inicio' },
  { to: '/modules', icon: BookOpen, label: 'Módulos' },
  { to: '/chat', icon: MessageCircle, label: 'Tutor IA' },
  { to: '/progress', icon: BarChart3, label: 'Mi progreso' },
  { to: '/achievements', icon: Trophy, label: 'Logros' },
]

const adminLinks = [
  { to: '/admin', icon: Settings, label: 'Administración' },
]

interface SidebarProps {
  open: boolean
  onClose: () => void
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  const user = useAuthStore((s) => s.user)
  const links = user?.role === 'admin' ? [...studentLinks, ...adminLinks] : studentLinks

  return (
    <>
      {/* Overlay for mobile */}
      {open && (
        <div
          className="fixed inset-0 bg-institutional-900/60 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        aria-label="Navegación principal"
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-white border-r border-gray-200 flex flex-col
                    transform transition-transform duration-200 lg:translate-x-0 lg:static lg:z-0
                    ${open ? 'translate-x-0' : '-translate-x-full'}`}
      >
        {/* Brand header with heritage accent */}
        <div className="relative">
          <div className="px-4 py-4 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <BrandLogo variant="stacked" />
              <button
                onClick={onClose}
                aria-label="Cerrar menú"
                className="lg:hidden text-gray-400 hover:text-gray-600 p-1 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
          <div className="heritage-accent-bar !w-full !h-[3px] !rounded-none" aria-hidden="true" />
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <p className="px-3 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
            Plataforma
          </p>
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors min-h-[44px] ${
                  isActive
                    ? 'bg-primary-50 text-primary-800 shadow-brand-sm'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              <link.icon className="w-5 h-5 shrink-0" aria-hidden="true" />
              <span>{link.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Institutional footer inside sidebar */}
        <div className="px-4 py-4 border-t border-gray-100 bg-gray-50/50">
          <p className="text-[11px] text-gray-500 leading-relaxed">
            IESTP <span className="font-semibold text-institutional-700">"República Federal de Alemania"</span>
          </p>
          <p className="text-[11px] text-gray-400 mt-0.5">Chiclayo · Perú</p>
        </div>
      </aside>
    </>
  )
}
