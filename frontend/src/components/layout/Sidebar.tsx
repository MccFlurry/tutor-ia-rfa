import { useEffect, useRef } from 'react'
import { NavLink, useMatch } from 'react-router-dom'
import {
  LayoutDashboard,
  BookOpen,
  MessageCircle,
  BarChart3,
  Trophy,
  Settings,
  SlidersHorizontal,
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
  { to: '/settings', icon: SlidersHorizontal, label: 'Ajustes' },
]

const adminLinks = [
  { to: '/admin', icon: Settings, label: 'Administración' },
]

/** Single nav item — uses useMatch so aria-current can be set imperatively. */
function NavItem({
  to,
  icon: Icon,
  label,
  onClick,
}: {
  to: string
  icon: React.ElementType
  label: string
  onClick: () => void
}) {
  const match = useMatch({ path: to, end: to === '/dashboard' })
  const isActive = Boolean(match)
  return (
    <NavLink
      to={to}
      onClick={onClick}
      aria-current={isActive ? 'page' : undefined}
      className={({ isActive: navActive }) =>
        `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors min-h-[44px] ${
          navActive
            ? 'bg-primary-50 text-primary-800 dark:bg-primary/15 dark:text-primary-200 shadow-brand-sm'
            : 'text-muted-foreground hover:bg-surface-hover hover:text-foreground'
        }`
      }
    >
      <Icon className="w-5 h-5 shrink-0" aria-hidden="true" />
      <span>{label}</span>
    </NavLink>
  )
}

interface SidebarProps {
  open: boolean
  onClose: () => void
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  const user = useAuthStore((s) => s.user)
  const links = user?.role === 'admin' ? [...studentLinks, ...adminLinks] : studentLinks
  const firstLinkRef = useRef<HTMLElement | null>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)

  // Mobile drawer: lock body scroll, handle Escape, move focus in.
  // These effects only matter when open===true, which is only toggled on mobile.
  useEffect(() => {
    if (!open) return
    // Lock scroll
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    // Escape key
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    // Focus close button (always present and labelled) when drawer opens
    closeButtonRef.current?.focus()
    return () => {
      document.body.style.overflow = prev
      document.removeEventListener('keydown', onKey)
    }
  }, [open, onClose])

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
        className={`fixed top-0 left-0 z-50 h-dvh w-64 bg-card border-r border-border flex flex-col
                    transform transition-transform duration-200 lg:translate-x-0 lg:sticky lg:top-0 lg:z-0
                    ${open ? 'translate-x-0' : '-translate-x-full'}`}
      >
        {/* Brand header with heritage accent */}
        <div className="relative">
          <div className="px-4 py-4 border-b border-border">
            <div className="flex items-center justify-between">
              <BrandLogo variant="stacked" />
              <button
                ref={closeButtonRef}
                type="button"
                onClick={onClose}
                aria-label="Cerrar menú"
                className="lg:hidden inline-flex items-center justify-center min-h-[44px] min-w-[44px]
                           text-muted-foreground hover:text-foreground rounded-lg
                           focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
          <div className="heritage-accent-bar !w-full !h-[3px] !rounded-none" aria-hidden="true" />
        </div>

        {/* Nav links */}
        <nav
          className="flex-1 px-3 py-4 space-y-1 overflow-y-auto"
          ref={(el) => {
            // Capture first focusable link for potential programmatic focus if needed
            firstLinkRef.current = el?.querySelector('a') ?? null
          }}
        >
          <p className="px-3 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Plataforma
          </p>
          {links.map((link) => (
            <NavItem
              key={link.to}
              to={link.to}
              icon={link.icon}
              label={link.label}
              onClick={onClose}
            />
          ))}
        </nav>

        {/* Institutional footer inside sidebar */}
        <div className="px-4 py-4 border-t border-border bg-muted/50">
          <p className="text-[11px] text-muted-foreground leading-relaxed">
            IESTP <span className="font-semibold text-institutional-700 dark:text-institutional-100">"República Federal de Alemania"</span>
          </p>
          <p className="text-[11px] text-muted-foreground mt-0.5">Chiclayo · Perú</p>
        </div>
      </aside>
    </>
  )
}
