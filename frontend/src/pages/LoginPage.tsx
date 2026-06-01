import { useState, useEffect, useCallback } from 'react'
import { useLogin, useRegister } from '@/hooks/useAuth'
import { Eye, EyeOff, Lock, GraduationCap, Sparkles, ShieldCheck, CheckCircle2 } from 'lucide-react'
import BrandLogo from '@/components/brand/BrandLogo'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

const MAX_ATTEMPTS = 3
const LOCKOUT_MS = 5 * 60 * 1000
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const PASSWORD_MIN = 6

type FieldKey = 'fullName' | 'email' | 'password'

function validateField(key: FieldKey, value: string, isRegister: boolean): string | null {
  switch (key) {
    case 'fullName':
      if (!isRegister) return null
      if (!value.trim()) return 'Ingresa tu nombre completo.'
      if (value.trim().length < 3) return 'El nombre debe tener al menos 3 caracteres.'
      return null
    case 'email':
      if (!value.trim()) return 'Ingresa tu correo electrónico.'
      if (!EMAIL_REGEX.test(value.trim())) return 'Correo no válido.'
      return null
    case 'password':
      if (!value) return 'Ingresa tu contraseña.'
      if (value.length < PASSWORD_MIN) return `Mínimo ${PASSWORD_MIN} caracteres.`
      return null
  }
}

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [failedAttempts, setFailedAttempts] = useState(0)
  const [lockoutUntil, setLockoutUntil] = useState<number | null>(null)
  const [remainingSeconds, setRemainingSeconds] = useState(0)
  const [errorMessage, setErrorMessage] = useState('')
  const [touched, setTouched] = useState<Record<FieldKey, boolean>>({
    fullName: false,
    email: false,
    password: false,
  })

  const loginMutation = useLogin()
  const registerMutation = useRegister()

  const isLocked = lockoutUntil !== null && Date.now() < lockoutUntil
  const isLoading = loginMutation.isPending || registerMutation.isPending

  // Per-field errors (only shown after touch)
  const fullNameError = touched.fullName ? validateField('fullName', fullName, isRegister) : null
  const emailError    = touched.email    ? validateField('email',    email,    isRegister) : null
  const passwordError = touched.password ? validateField('password', password, isRegister) : null

  // Submit is enabled only when all current-mode fields are valid
  const allValid =
    validateField('email', email, isRegister) === null &&
    validateField('password', password, isRegister) === null &&
    (!isRegister || validateField('fullName', fullName, isRegister) === null)

  useEffect(() => {
    if (!lockoutUntil) return
    const tick = () => {
      const diff = Math.ceil((lockoutUntil - Date.now()) / 1000)
      if (diff <= 0) {
        setLockoutUntil(null)
        setFailedAttempts(0)
        setRemainingSeconds(0)
        setErrorMessage('')
      } else {
        setRemainingSeconds(diff)
      }
    }
    tick()
    const interval = setInterval(tick, 1000)
    return () => clearInterval(interval)
  }, [lockoutUntil])

  const handleLoginError = useCallback(() => {
    const newAttempts = failedAttempts + 1
    setFailedAttempts(newAttempts)
    setErrorMessage('Credenciales incorrectas. Verifica tus datos.')
    if (newAttempts >= MAX_ATTEMPTS) {
      setLockoutUntil(Date.now() + LOCKOUT_MS)
      setErrorMessage('')
    }
  }, [failedAttempts])

  const markAllTouched = () =>
    setTouched({ fullName: true, email: true, password: true })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage('')
    markAllTouched()
    if (!allValid) return

    if (isRegister) {
      registerMutation.mutate(
        { email, full_name: fullName, password },
        {
          onError: (err: any) => {
            setErrorMessage(
              err?.response?.data?.detail || 'No se pudo crear la cuenta.'
            )
          },
        }
      )
    } else {
      loginMutation.mutate({ email, password }, { onError: () => handleLoginError() })
    }
  }

  const handleToggleMode = () => {
    setIsRegister(!isRegister)
    setErrorMessage('')
    setTouched({ fullName: false, email: false, password: false })
  }

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  // Class + a11y wiring helper for each input
  const fieldProps = (key: FieldKey, hasError: boolean, helpId?: string) => ({
    'aria-invalid': hasError || undefined,
    'aria-describedby': hasError ? `${key}-error` : helpId,
    className: cn(hasError && 'border-destructive focus-visible:border-destructive focus-visible:ring-destructive/30'),
    onBlur: () => setTouched((t) => ({ ...t, [key]: true })),
  })

  return (
    <div className="min-h-dvh grid lg:grid-cols-2">
      <aside
        className="hidden lg:flex flex-col justify-between relative p-12 bg-brand-hero text-white overflow-hidden"
        aria-hidden="true"
      >
        <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-primary-500/20 blur-3xl" />
        <div className="absolute -bottom-32 -right-32 w-[28rem] h-[28rem] rounded-full bg-primary-500/10 blur-3xl" />

        <div className="relative">
          <BrandLogo variant="stacked" onDark size={64} />
        </div>

        <div className="relative">
          <span className="heritage-accent-bar mb-6" />
          <h2 className="text-3xl xl:text-4xl font-extrabold leading-tight mb-4">
            Sistema de Tutoría Inteligente para Aplicaciones Móviles.
          </h2>
          <p className="text-primary-100 max-w-md leading-relaxed">
            Estudia Android con Kotlin acompañado por un tutor de IA privado
            entrenado con el corpus oficial del instituto.
          </p>

          <ul className="mt-8 space-y-3 text-sm">
            <li className="flex items-center gap-3">
              <GraduationCap className="w-5 h-5 text-primary-300 shrink-0" />
              <span>5 módulos · 22 temas · 45 desafíos de programación</span>
            </li>
            <li className="flex items-center gap-3">
              <Sparkles className="w-5 h-5 text-primary-300 shrink-0" />
              <span>IA generativa adaptada a tu nivel</span>
            </li>
            <li className="flex items-center gap-3">
              <ShieldCheck className="w-5 h-5 text-primary-300 shrink-0" />
              <span>100% privado — datos institucionales protegidos</span>
            </li>
          </ul>
        </div>

        <div className="relative text-xs text-primary-200">
          IESTP "República Federal de Alemania" · Chiclayo, Perú
          <div className="text-primary-300">Tesis de pregrado — USAT</div>
        </div>
      </aside>

      <main className="flex items-center justify-center px-4 py-6 sm:p-10 bg-gradient-to-br from-muted to-background">
        <div className="w-full max-w-md">
          <div className="lg:hidden mb-6 flex justify-center">
            <BrandLogo variant="stacked" size={56} />
          </div>

          <div className="bg-card rounded-2xl shadow-brand-lg border border-border p-5 sm:p-8 animate-fade-in-up">
            <header className="mb-6">
              <span className="chip bg-primary-100 text-primary-700 dark:bg-primary/20 dark:text-primary-200 mb-3">
                {isRegister ? 'Nuevo estudiante' : 'Portal del estudiante'}
              </span>
              <h1 className="text-2xl font-extrabold text-institutional-700 dark:text-institutional-100">
                {isRegister ? 'Crea tu cuenta' : 'Inicia sesión'}
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                {isRegister
                  ? 'Completa tus datos para comenzar la evaluación de entrada.'
                  : 'Accede con tu correo institucional o personal.'}
              </p>
            </header>

            {errorMessage && !isLocked && (
              <div
                role="alert"
                aria-live="polite"
                className="mb-4 p-3 bg-peru-50 dark:bg-peru-700/20 border border-peru-500/30 rounded-lg text-sm text-peru-700 dark:text-peru-300"
              >
                {errorMessage}
                {failedAttempts > 0 && failedAttempts < MAX_ATTEMPTS && !isRegister && (
                  <span className="block text-xs text-peru-600 dark:text-peru-400 mt-1">
                    Intentos restantes: {MAX_ATTEMPTS - failedAttempts}
                  </span>
                )}
              </div>
            )}

            {isLocked && (
              <div
                role="alert"
                aria-live="assertive"
                className="mb-4 p-4 bg-peru-50 dark:bg-peru-700/20 border border-peru-500/30 rounded-lg text-center"
              >
                <Lock className="w-5 h-5 text-peru-600 dark:text-peru-400 mx-auto mb-2" aria-hidden="true" />
                <p className="text-sm font-semibold text-peru-700 dark:text-peru-300">
                  Demasiados intentos fallidos
                </p>
                <p className="text-xs text-peru-600 dark:text-peru-400 mt-1">
                  Inténtalo nuevamente en{' '}
                  <span className="font-mono">{formatTime(remainingSeconds)}</span>
                </p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              {isRegister && (
                <div className="space-y-1.5">
                  <Label htmlFor="fullName">Nombre completo</Label>
                  <Input
                    id="fullName"
                    type="text"
                    required
                    autoComplete="name"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Juan Pérez"
                    {...fieldProps('fullName', !!fullNameError)}
                  />
                  {fullNameError && (
                    <p id="fullName-error" className="text-xs text-destructive" role="alert">
                      {fullNameError}
                    </p>
                  )}
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="email">Correo electrónico</Label>
                <div className="relative">
                  <Input
                    id="email"
                    type="email"
                    required
                    autoComplete="email"
                    inputMode="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="estudiante@iestprfa.edu.pe"
                    disabled={isLocked}
                    {...fieldProps('email', !!emailError, 'email-help')}
                    className={cn(
                      fieldProps('email', !!emailError).className,
                      touched.email && !emailError && 'pr-10'
                    )}
                  />
                  {touched.email && !emailError && email && (
                    <CheckCircle2
                      className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-success pointer-events-none"
                      aria-hidden="true"
                    />
                  )}
                </div>
                {emailError && (
                  <p id="email-error" className="text-xs text-destructive" role="alert">
                    {emailError}
                  </p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="password">Contraseña</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    minLength={PASSWORD_MIN}
                    autoComplete={isRegister ? 'new-password' : 'current-password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={`Mínimo ${PASSWORD_MIN} caracteres`}
                    disabled={isLocked}
                    {...fieldProps('password', !!passwordError, 'password-help')}
                    className={cn(
                      fieldProps('password', !!passwordError).className,
                      'pr-12'
                    )}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                    aria-pressed={showPassword}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground rounded-md
                               inline-flex items-center justify-center min-h-[44px] min-w-[44px]
                               focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    {showPassword ? (
                      <EyeOff className="w-5 h-5" aria-hidden="true" />
                    ) : (
                      <Eye className="w-5 h-5" aria-hidden="true" />
                    )}
                  </button>
                </div>
                {passwordError ? (
                  <p id="password-error" className="text-xs text-destructive" role="alert">
                    {passwordError}
                  </p>
                ) : (
                  <p id="password-help" className="text-xs text-muted-foreground">
                    Mínimo {PASSWORD_MIN} caracteres.
                  </p>
                )}
              </div>

              <button
                type="submit"
                disabled={isLoading || isLocked}
                className="w-full h-11 bg-institutional-700 hover:bg-institutional-500 dark:bg-primary dark:hover:bg-primary/90 text-white dark:text-primary-foreground font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed shadow-brand-md
                           focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                {isLocked
                  ? `Bloqueado (${formatTime(remainingSeconds)})`
                  : isLoading
                    ? 'Procesando...'
                    : isRegister
                      ? 'Crear cuenta'
                      : 'Ingresar'}
              </button>
            </form>

            <div className="mt-6 text-center">
              <button
                type="button"
                onClick={handleToggleMode}
                className="text-sm text-primary-700 hover:text-primary-800 dark:text-primary-300 dark:hover:text-primary-200 font-semibold underline-offset-4 hover:underline
                           inline-flex items-center justify-center min-h-[44px] px-3
                           focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-md"
              >
                {isRegister
                  ? '¿Ya tienes cuenta? Inicia sesión'
                  : '¿Primera vez? Crea tu cuenta'}
              </button>
            </div>

            {!isRegister && (
              <p className="mt-3 text-center text-xs text-muted-foreground">
                ¿Olvidaste tu contraseña? Escribe al administrador del instituto.
              </p>
            )}
          </div>

          <p className="text-center text-muted-foreground text-xs mt-6 lg:hidden">
            IESTP "República Federal de Alemania" · Chiclayo, Perú
          </p>
        </div>
      </main>
    </div>
  )
}
