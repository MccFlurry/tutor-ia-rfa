import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'
import Sidebar from './Sidebar'
import Footer from './Footer'
import ReassessmentModal from '@/components/auth/ReassessmentModal'

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <a href="#main-content" className="skip-link">
        Saltar al contenido principal
      </a>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col min-h-dvh">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main id="main-content" className="flex-1 overflow-auto focus:outline-none" tabIndex={-1}>
          <Outlet />
        </main>
        <Footer />
      </div>
      <ReassessmentModal />
    </div>
  )
}
