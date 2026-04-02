import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'
import { usersApi } from '@/api/users'
import AuthGuard from '@/components/auth/AuthGuard'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'

function App() {
  const { loadFromStorage, isAuthenticated, user, setUser, logout } = useAuthStore()

  useEffect(() => {
    loadFromStorage()
  }, [loadFromStorage])

  // Fetch user profile when we have a token but no user data (page refresh)
  useEffect(() => {
    if (isAuthenticated && !user) {
      usersApi.getMe()
        .then(({ data }) => setUser(data))
        .catch(() => logout())
    }
  }, [isAuthenticated, user, setUser, logout])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/dashboard"
          element={
            <AuthGuard>
              <DashboardPage />
            </AuthGuard>
          }
        />
      </Routes>
      <Toaster position="top-right" />
    </BrowserRouter>
  )
}

export default App
