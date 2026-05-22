import * as React from 'react'
import { AlertTriangle, RefreshCw, ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

interface FallbackProps {
  error: Error
  reset: () => void
}

function FallbackShell({
  title,
  message,
  primaryAction,
  secondaryAction,
}: {
  title: string
  message: string
  primaryAction: React.ReactNode
  secondaryAction: React.ReactNode
}) {
  return (
    <div className="max-w-md mx-auto py-12 px-4 text-center">
      <div
        className="w-14 h-14 mx-auto bg-destructive/10 rounded-full flex items-center justify-center mb-4"
        aria-hidden="true"
      >
        <AlertTriangle className="w-7 h-7 text-destructive" />
      </div>
      <h2 className="text-lg font-bold text-foreground mb-2" role="alert">
        {title}
      </h2>
      <p className="text-sm text-muted-foreground mb-6">{message}</p>
      <div className="flex flex-col sm:flex-row gap-2 justify-center">
        {primaryAction}
        {secondaryAction}
      </div>
    </div>
  )
}

const primaryBtn =
  'inline-flex items-center justify-center gap-2 min-h-[44px] px-4 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 font-semibold text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2'

const secondaryBtn =
  'inline-flex items-center justify-center gap-2 min-h-[44px] px-4 rounded-lg border border-input bg-background hover:bg-accent text-foreground font-semibold text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2'

export function ChatErrorFallback({ reset }: FallbackProps) {
  return (
    <FallbackShell
      title="Error en el chat"
      message="Tus sesiones están seguras. Reintenta para continuar la conversación."
      primaryAction={
        <button type="button" onClick={reset} className={primaryBtn}>
          <RefreshCw className="w-4 h-4" />
          Reintentar
        </button>
      }
      secondaryAction={
        <Link to="/dashboard" className={secondaryBtn}>
          <ArrowLeft className="w-4 h-4" />
          Volver al inicio
        </Link>
      }
    />
  )
}

export function QuizErrorFallback({ reset }: FallbackProps) {
  return (
    <FallbackShell
      title="Error generando el quiz"
      message="Puedes intentarlo de nuevo o regresar al tema."
      primaryAction={
        <button type="button" onClick={reset} className={primaryBtn}>
          <RefreshCw className="w-4 h-4" />
          Reintentar
        </button>
      }
      secondaryAction={
        <Link to="/modules" className={secondaryBtn}>
          <ArrowLeft className="w-4 h-4" />
          Ir a módulos
        </Link>
      }
    />
  )
}

export function CodingErrorFallback({ reset }: FallbackProps) {
  return (
    <FallbackShell
      title="Error cargando el desafío"
      message="Reintenta o regresa al tema asociado."
      primaryAction={
        <button type="button" onClick={reset} className={primaryBtn}>
          <RefreshCw className="w-4 h-4" />
          Reintentar
        </button>
      }
      secondaryAction={
        <Link to="/modules" className={secondaryBtn}>
          <ArrowLeft className="w-4 h-4" />
          Ir a módulos
        </Link>
      }
    />
  )
}
