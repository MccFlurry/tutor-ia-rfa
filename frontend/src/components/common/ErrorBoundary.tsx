import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: (error: Error, reset: () => void) => ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

/**
 * Global React error boundary. Catches render-phase exceptions and shows a
 * friendly Spanish fallback instead of a white screen. Async errors (Promise
 * rejections, event handlers) are NOT caught — handle those locally.
 */
export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // eslint-disable-next-line no-console
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  reset = (): void => {
    this.setState({ hasError: false, error: null })
  }

  render(): ReactNode {
    if (!this.state.hasError) return this.props.children
    if (this.props.fallback && this.state.error) {
      return this.props.fallback(this.state.error, this.reset)
    }

    const isDev = import.meta.env.DEV

    return (
      <div className="min-h-dvh flex items-center justify-center bg-background px-4 py-10">
        <div
          role="alert"
          className="max-w-md w-full bg-card rounded-2xl border border-border shadow-brand-lg p-8 text-center"
        >
          <div
            className="w-16 h-16 mx-auto bg-destructive/10 rounded-full flex items-center justify-center mb-4"
            aria-hidden="true"
          >
            <AlertTriangle className="w-8 h-8 text-destructive" />
          </div>
          <h1 className="text-xl font-bold text-foreground mb-2">
            Algo salió mal
          </h1>
          <p className="text-sm text-muted-foreground mb-6">
            Ocurrió un error inesperado. Recarga la página para continuar.
            Si el problema persiste, contacta al administrador.
          </p>

          {isDev && this.state.error && (
            <details className="text-left text-xs bg-muted rounded-lg p-3 mb-4 max-h-32 overflow-auto">
              <summary className="cursor-pointer font-mono text-muted-foreground">
                Detalle (solo en desarrollo)
              </summary>
              <pre className="mt-2 whitespace-pre-wrap break-words text-foreground">
                {this.state.error.message}
                {this.state.error.stack && '\n\n' + this.state.error.stack}
              </pre>
            </details>
          )}

          <div className="flex flex-col sm:flex-row gap-2 justify-center">
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="inline-flex items-center justify-center gap-2 h-11 px-4 rounded-lg
                         bg-primary text-primary-foreground hover:bg-primary/90 font-semibold text-sm
                         focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <RefreshCw className="w-4 h-4" />
              Recargar
            </button>
            <button
              type="button"
              onClick={() => {
                this.reset()
                window.location.href = '/dashboard'
              }}
              className="inline-flex items-center justify-center gap-2 h-11 px-4 rounded-lg
                         border border-input bg-background hover:bg-accent font-semibold text-sm text-foreground
                         focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <Home className="w-4 h-4" />
              Ir al inicio
            </button>
          </div>
        </div>
      </div>
    )
  }
}
