import { useAuthStore } from '@/store/authStore'
import { useLogout } from '@/hooks/useAuth'
import { LogOut } from 'lucide-react'

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const logout = useLogout()

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Tutor IA — IESTP RFA</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">
            {user?.full_name}
          </span>
          <button
            onClick={logout}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-red-600 transition"
          >
            <LogOut className="w-4 h-4" />
            Salir
          </button>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-6 py-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          ¡Hola de nuevo, {user?.full_name?.split(' ')[0]}!
        </h2>
        <p className="text-gray-500">
          Bienvenido al Sistema de Tutoría Inteligente para Aplicaciones Móviles.
        </p>
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <p className="text-sm text-gray-500">Progreso general</p>
            <p className="text-3xl font-bold text-primary-600 mt-1">0%</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <p className="text-sm text-gray-500">Lecciones completadas</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">0</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <p className="text-sm text-gray-500">Promedio en quizzes</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">—</p>
          </div>
        </div>
      </main>
    </div>
  )
}
