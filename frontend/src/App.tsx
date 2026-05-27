import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'
import { useThemeStore } from '@/store/themeStore'
import { useMediaQuery } from '@/hooks/useMediaQuery'
import { usersApi } from '@/api/users'
import ErrorBoundary from '@/components/common/ErrorBoundary'
import {
  ChatErrorFallback,
  QuizErrorFallback,
  CodingErrorFallback,
} from '@/components/common/RouteErrorFallbacks'
import AuthGuard from '@/components/auth/AuthGuard'
import LevelGuard from '@/components/auth/LevelGuard'
import AppLayout from '@/components/layout/AppLayout'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import ModulesPage from '@/pages/ModulesPage'
import ModuleDetailPage from '@/pages/ModuleDetailPage'
import TopicPage from '@/pages/TopicPage'
import QuizPage from '@/pages/QuizPage'
import ProgressPage from '@/pages/ProgressPage'
import AchievementsPage from '@/pages/AchievementsPage'
import ChatPage from '@/pages/ChatPage'
import CodingChallengePage from '@/pages/CodingChallengePage'
import EntryAssessmentPage from '@/pages/EntryAssessmentPage'
import SettingsPage from '@/pages/SettingsPage'
import AdminPage from '@/pages/AdminPage'
import AdminStudentReportPage from '@/pages/AdminStudentReportPage'

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

      {/* Entry assessment: authenticated but no level required */}
      <Route
        path="/assessment"
        element={
          <AuthGuard>
            <EntryAssessmentPage />
          </AuthGuard>
        }
      />

      {/* Authenticated routes with layout + level requirement */}
      <Route
        element={
          <AuthGuard>
            <LevelGuard>
              <AppLayout />
            </LevelGuard>
          </AuthGuard>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/modules" element={<ModulesPage />} />
        <Route path="/modules/:id" element={<ModuleDetailPage />} />
        <Route path="/topics/:id" element={<TopicPage />} />
        <Route
          path="/quiz/:topicId"
          element={
            <ErrorBoundary
              fallback={(error, reset) => (
                <QuizErrorFallback error={error} reset={reset} />
              )}
            >
              <QuizPage />
            </ErrorBoundary>
          }
        />
        <Route path="/progress" element={<ProgressPage />} />
        <Route path="/achievements" element={<AchievementsPage />} />
        <Route
          path="/chat"
          element={
            <ErrorBoundary
              fallback={(error, reset) => (
                <ChatErrorFallback error={error} reset={reset} />
              )}
            >
              <ChatPage />
            </ErrorBoundary>
          }
        />
        <Route
          path="/coding/:challengeId"
          element={
            <ErrorBoundary
              fallback={(error, reset) => (
                <CodingErrorFallback error={error} reset={reset} />
              )}
            >
              <CodingChallengePage />
            </ErrorBoundary>
          }
        />
        <Route path="/settings" element={<SettingsPage />} />
        <Route
          path="/admin"
          element={
            <AuthGuard requireAdmin>
              <AdminPage />
            </AuthGuard>
          }
        />
        <Route
          path="/admin/students/:userId"
          element={
            <AuthGuard requireAdmin>
              <AdminStudentReportPage />
            </AuthGuard>
          }
        />
      </Route>
    </Routes>
  )
}

function App() {
  const isDesktop = useMediaQuery('(min-width: 640px)')
  const initTheme = useThemeStore((s) => s.init)
  const isDark = useThemeStore((s) => s.isDark)

  useEffect(() => {
    const cleanup = initTheme()
    return cleanup
  }, [initTheme])

  const toastStyle = isDark
    ? { background: 'hsl(222 47% 9%)', color: 'hsl(210 40% 96%)', border: '1px solid hsl(217 33% 22%)' }
    : { background: '#ffffff', color: 'hsl(222 47% 11%)', border: '1px solid hsl(214 32% 91%)' }

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AppRoutes />
        <Toaster
          position={isDesktop ? 'top-right' : 'top-center'}
          toastOptions={{
            style: toastStyle,
            success: { ariaProps: { role: 'status', 'aria-live': 'polite' } },
            error:   { ariaProps: { role: 'alert',  'aria-live': 'assertive' } },
            blank:   { ariaProps: { role: 'status', 'aria-live': 'polite' } },
            loading: { ariaProps: { role: 'status', 'aria-live': 'polite' } },
          }}
        />
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
