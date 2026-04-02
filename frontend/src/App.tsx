import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'
import { usersApi } from '@/api/users'
import AuthGuard from '@/components/auth/AuthGuard'
import AppLayout from '@/components/layout/AppLayout'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import ModulesPage from '@/pages/ModulesPage'
import ModuleDetailPage from '@/pages/ModuleDetailPage'
import TopicPage from '@/pages/TopicPage'
import QuizPage from '@/pages/QuizPage'
import ProgressPage from '@/pages/ProgressPage'
import AchievementsPage from '@/pages/AchievementsPage'

function AppRoutes() {
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
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/login" element={<LoginPage />} />

      {/* Authenticated routes with layout */}
      <Route
        element={
          <AuthGuard>
            <AppLayout />
          </AuthGuard>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/modules" element={<ModulesPage />} />
        <Route path="/modules/:id" element={<ModuleDetailPage />} />
        <Route path="/topics/:id" element={<TopicPage />} />
        <Route path="/quiz/:topicId" element={<QuizPage />} />
        <Route path="/progress" element={<ProgressPage />} />
        <Route path="/achievements" element={<AchievementsPage />} />
      </Route>
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
      <Toaster position="top-right" />
    </BrowserRouter>
  )
}

export default App
