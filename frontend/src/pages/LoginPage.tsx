import { useState, useEffect, useCallback } from 'react'
import { useLogin, useRegister } from '@/hooks/useAuth'
import { Eye, EyeOff, Smartphone, Lock } from 'lucide-react'

const MAX_ATTEMPTS = 3
const LOCKOUT_MS = 5 * 60 * 1000 // 5 minutes

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

  // Countdown timer for lockout
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
    setErrorMessage('Credenciales incorrectas, inténtelo de nuevo')

    if (newAttempts >= MAX_ATTEMPTS) {
      const until = Date.now() + LOCKOUT_MS
      setLockoutUntil(until)
      setErrorMessage('')
    }
  }, [failedAttempts])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage('')

    if (isRegister) {
      registerMutation.mutate({ email, full_name: fullName, password })
    } else {
      loginMutation.mutate(
        { email, password },
        {
          onError: () => handleLoginError(),
        },
      )
    }
  }

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-900 via-primary-800 to-primary-700 px-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
              <Smartphone className="w-8 h-8 text-primary-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">
              Sistema de Tutoría Inteligente
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Curso de Aplicaciones Móviles — IESTP RFA
            </p>
          </div>

          {/* Error message */}
          {errorMessage && !isLocked && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 text-center">
              {errorMessage}
              {failedAttempts > 0 && failedAttempts < MAX_ATTEMPTS && (
                <span className="block text-xs text-red-500 mt-1">
                  Intentos restantes: {MAX_ATTEMPTS - failedAttempts}
                </span>
              )}
            </div>
          )}

          {/* Lockout message */}
          {isLocked && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-center">
              <Lock className="w-5 h-5 text-red-500 mx-auto mb-2" />
              <p className="text-sm font-medium text-red-700">
                Demasiados intentos fallidos
              </p>
              <p className="text-xs text-red-500 mt-1">
                Inténtelo de nuevo en {formatTime(remainingSeconds)}
              </p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label htmlFor="fullName" className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre completo
                </label>
                <input
                  id="fullName"
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Juan Pérez"
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                />
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Correo electrónico
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="estudiante@ejemplo.com"
                disabled={isLocked}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition disabled:bg-gray-100 disabled:text-gray-400"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Contraseña
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  minLength={6}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={isLocked}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition pr-12 disabled:bg-gray-100 disabled:text-gray-400"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || isLocked}
              className="w-full py-2.5 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
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

          {/* Toggle */}
          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => {
                setIsRegister(!isRegister)
                setErrorMessage('')
              }}
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              {isRegister
                ? '¿Ya tienes cuenta? Inicia sesión'
                : '¿No tienes cuenta? Regístrate'}
            </button>
          </div>
        </div>

        <p className="text-center text-primary-200 text-xs mt-6">
          IESTP "República Federal de Alemania" — Chiclayo, Perú
        </p>
      </div>
    </div>
  )
}
