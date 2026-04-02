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

const studentLinks = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Inicio' },
  { to: '/modules', icon: BookOpen, label: 'Módulos' },
  { to: '/chat', icon: MessageCircle, label: 'Tutor IA' },
  { to: '/progress', icon: BarChart3, label: 'Mi Progreso' },
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
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-white border-r border-gray-200 transform transition-transform duration-200 lg:translate-x-0 lg:static lg:z-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <span className="text-xl">📱</span>
            <span className="font-bold text-gray-900 text-sm">Tutor IA — RFA</span>
          </div>
          <button onClick={onClose} className="lg:hidden text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav links */}
        <nav className="px-3 py-4 space-y-1">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`
              }
            >
              <link.icon className="w-5 h-5 shrink-0" />
              {link.label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  )
}
