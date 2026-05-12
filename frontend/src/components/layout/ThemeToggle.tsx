import { Sun, Moon, Monitor } from 'lucide-react'
import { useThemeStore, type ThemePref } from '@/store/themeStore'

const NEXT_PREF: Record<ThemePref, ThemePref> = {
  light: 'dark',
  dark: 'system',
  system: 'light',
}

const LABEL: Record<ThemePref, string> = {
  light: 'Tema claro (cambiar a oscuro)',
  dark: 'Tema oscuro (cambiar a sistema)',
  system: 'Tema del sistema (cambiar a claro)',
}

export default function ThemeToggle() {
  const pref = useThemeStore((s) => s.pref)
  const setPref = useThemeStore((s) => s.setPref)

  const Icon = pref === 'light' ? Sun : pref === 'dark' ? Moon : Monitor

  return (
    <button
      type="button"
      onClick={() => setPref(NEXT_PREF[pref])}
      aria-label={LABEL[pref]}
      title={LABEL[pref]}
      className="inline-flex items-center justify-center min-h-[44px] min-w-[44px]
                 text-muted-foreground hover:text-foreground rounded-lg
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring transition-colors"
    >
      <Icon className="w-5 h-5" aria-hidden="true" />
    </button>
  )
}
