import { useState, useEffect, useCallback } from 'react'
import { useLogin, useRegister } from '@/hooks/useAuth'
import { Eye, EyeOff, Lock, GraduationCap, Sparkles, ShieldCheck } from 'lucide-react'
import BrandLogo from '@/components/brand/BrandLogo'

const MAX_ATTEMPTS = 3
const LOCKOUT_MS = 5 * 60 * 1000

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

  const loginMutation = useLogin()
  const registerMutation = useRegister()

  const isLocked = lockoutUntil !== null && Date.now() < lockoutUntil
  const isLoading = loginMutation.isPending || registerMutation.isPending

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage('')
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

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  return (
    <div className="min-h-dvh grid lg:grid-cols-2">
      {/* Left: institutional brand panel (hidden on mobile) */}
      <aside
        className="hidden lg:flex flex-col justify-between relative p-12 bg-brand-hero text-white overflow-hidden"
        aria-hidden="true"
      >
        {/* Decorative orbs */}
        <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-primary-500/20 blur-3xl" />
        <div className="absolute -bottom-32 -right-32 w-[28rem] h-[28rem] rounded-full bg-heritage-500/10 blur-3xl" />

        <div className="relative">
          <BrandLogo variant="stacked" onDark />
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
              <GraduationCap className="w-5 h-5 text-heritage-400 shrink-0" />
              <span>5 módulos · 22 temas · 7 desafíos de programación</span>
            </li>
            <li className="flex items-center gap-3">
              <Sparkles className="w-5 h-5 text-heritage-400 shrink-0" />
              <span>IA generativa adaptada a tu nivel</span>
            </li>
            <li className="flex items-center gap-3">
              <ShieldCheck className="w-5 h-5 text-heritage-400 shrink-0" />
              <span>100% privado — datos institucionales protegidos</span>
            </li>
          </ul>
        </div>

        <div className="relative text-xs text-primary-200">
          IESTP "República Federal de Alemania" · Chiclayo, Perú
          <div className="text-primary-300">Tesis de pregrado — USAT</div>
        </div>
      </aside>

      {/* Right: form */}
      <main className="flex items-center justify-center p-6 sm:p-10 bg-gradient-to-br from-gray-50 to-white">
        <div className="w-full max-w-md">
          {/* Mobile brand header */}
          <div className="lg:hidden mb-6 flex justify-center">
            <BrandLogo variant="stacked" />
          </div>

          <div className="bg-white rounded-2xl shadow-brand-lg border border-gray-100 p-6 sm:p-8 animate-fade-in-up">
            <header className="mb-6">
              <span className="chip bg-heritage-100 text-heritage-700 mb-3">
                {isRegister ? 'Nuevo estudiante' : 'Portal del estudiante'}
              </span>
              <h1 className="text-2xl font-extrabold text-institutional-700">
                {isRegister ? 'Crea tu cuenta' : 'Inicia sesión'}
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                {isRegister
                  ? 'Completa tus datos para comenzar la evaluación de entrada.'
                  : 'Accede con tu correo institucional o personal.'}
              </p>
            </header>

            {errorMessage && !isLocked && (
              <div
                role="alert"
                className="mb-4 p-3 bg-peru-50 border border-peru-500/30 rounded-lg text-sm text-peru-700"
              >
                {errorMessage}
                {failedAttempts > 0 && failedAttempts < MAX_ATTEMPTS && !isRegister && (
                  <span className="block text-xs text-peru-600 mt-1">
                    Intentos restantes: {MAX_ATTEMPTS - failedAttempts}
                  </span>
                )}
              </div>
            )}

            {isLocked && (
              <div
                role="alert"
                className="mb-4 p-4 bg-peru-50 border border-peru-500/30 rounded-lg text-center"
              >
                <Lock className="w-5 h-5 text-peru-600 mx-auto mb-2" aria-hidden="true" />
                <p className="text-sm font-semibold text-peru-700">
                  Demasiados intentos fallidos
                </p>
                <p className="text-xs text-peru-600 mt-1">
                  Inténtalo nuevamente en{' '}
                  <span className="font-mono">{formatTime(remainingSeconds)}</span>
                </p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              {isRegister && (
                <div>
                  <label
                    htmlFor="fullName"
                    className="block text-sm font-semibold text-gray-700 mb-1.5"
                  >
                    Nombre completo
                  </label>
                  <input
                    id="fullName"
                    type="text"
                    required
                    autoComplete="name"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Juan Pérez"
                    className="w-full h-11 px-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition text-base"
                  />
                </div>
              )}

              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-semibold text-gray-700 mb-1.5"
                >
                  Correo electrónico
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  autoComplete="email"
                  inputMode="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="estudiante@iestprfa.edu.pe"
                  disabled={isLocked}
                  className="w-full h-11 px-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition text-base disabled:bg-gray-100 disabled:text-gray-400"
                />
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-semibold text-gray-700 mb-1.5"
                >
                  Contraseña
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    minLength={6}
                    autoComplete={isRegister ? 'new-password' : 'current-password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Mínimo 6 caracteres"
                    disabled={isLocked}
                    className="w-full h-11 px-4 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition text-base disabled:bg-gray-100 disabled:text-gray-400"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                    aria-pressed={showPassword}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 p-2 rounded"
                  >
                    {showPassword ? (
                      <EyeOff className="w-5 h-5" aria-hidden="true" />
                    ) : (
                      <Eye className="w-5 h-5" aria-hidden="true" />
                    )}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading || isLocked}
                className="w-full h-11 bg-institutional-700 hover:bg-institutional-500 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed shadow-brand-md"
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
                onClick={() => {
                  setIsRegister(!isRegister)
                  setErrorMessage('')
                }}
                className="text-sm text-primary-700 hover:text-primary-800 font-semibold underline-offset-4 hover:underline"
              >
                {isRegister
                  ? '¿Ya tienes cuenta? Inicia sesión'
                  : '¿Primera vez? Crea tu cuenta'}
              </button>
            </div>
          </div>

          <p className="text-center text-gray-400 text-xs mt-6 lg:hidden">
            IESTP "República Federal de Alemania" · Chiclayo, Perú
          </p>
        </div>
      </main>
    </div>
  )
}
