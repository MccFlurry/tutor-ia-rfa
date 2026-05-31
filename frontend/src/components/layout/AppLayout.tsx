import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'
import Sidebar from './Sidebar'
import Footer from './Footer'
import ReassessmentModal from '@/components/auth/ReassessmentModal'
import PageTransition from '@/components/common/PageTransition'
import { useFocusMain } from '@/hooks/useFocusMain'
import FloatingTutor from '@/components/tutor/FloatingTutor'

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  useFocusMain()

  return (
    <div className="min-h-screen bg-background flex">
      <a href="#main-content" className="skip-link">
        Saltar al contenido principal
      </a>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col min-h-dvh">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main id="main-content" className="flex-1 overflow-auto focus:outline-none" tabIndex={-1}>
          <PageTransition>
            <Outlet />
          </PageTransition>
        </main>
        <Footer />
      </div>
      <ReassessmentModal />
      <FloatingTutor />
    </div>
  )
}
