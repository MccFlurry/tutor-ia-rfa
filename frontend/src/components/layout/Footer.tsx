import { useLocation } from 'react-router-dom'

const DENSE_ROUTE_PREFIXES = ['/chat', '/coding']

export default function Footer() {
  const { pathname } = useLocation()
  const isDenseRoute = DENSE_ROUTE_PREFIXES.some((prefix) => pathname.startsWith(prefix))
  if (isDenseRoute) return null

  const year = new Date().getFullYear()
  return (
    <footer
      role="contentinfo"
      className="border-t border-border bg-card px-4 py-4 sm:px-6 text-xs text-muted-foreground flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:justify-between"
    >
      <p>
        © {year}{' '}
        <span className="font-semibold text-institutional-700 dark:text-institutional-100">
          IESTP "República Federal de Alemania"
        </span>{' '}
        — Chiclayo, Perú
      </p>
      <p className="text-muted-foreground">
        Tesis USAT · Sistema de Tutoría Inteligente con IA Generativa
      </p>
    </footer>
  )
}
