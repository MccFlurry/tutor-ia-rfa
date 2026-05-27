import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import AdminStudentReportPage from './AdminStudentReportPage'
import { adminReportsApi } from '@/api/adminReports'

vi.mock('@/api/adminReports', () => ({
  adminReportsApi: {
    getDetail: vi.fn(),
    generateReport: vi.fn(),
  },
}))

vi.mock('@/lib/reportPdf', () => ({
  generateReportPDF: vi.fn().mockResolvedValue(undefined),
}))
import { generateReportPDF } from '@/lib/reportPdf'

function wrap(initialPath: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/admin/students/:userId" element={<AdminStudentReportPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

const detail = {
  user_id: 'u1', full_name: 'Ana', email: 'a@x',
  created_at: '2026-01-01T00:00:00Z', is_active: true,
  level: 'beginner', entry_score: 50, level_history: [],
  overall_progress_pct: 60,
  modules: [{ module_id: 1, module_title: 'M1', topics_total: 4,
              topics_completed: 2, progress_pct: 50,
              avg_quiz_score: 0.5, avg_coding_score: null }],
  recent_quizzes: [],
  recent_coding: [],
  chat_messages_count: 3,
  chat_last_at: null,
  achievements_earned: [],
  total_time_seconds: 120,
  last_activity_at: '2026-05-20T10:00:00Z',
  last_location: 'M1 - Intro',
}

describe('AdminStudentReportPage', () => {
  it('renders detail sections when loaded', async () => {
    ;(adminReportsApi.getDetail as any).mockResolvedValue({ data: detail })
    render(wrap('/admin/students/u1'))
    expect(await screen.findByText('Ana')).toBeInTheDocument()
    expect(screen.getAllByText(/M1/).length).toBeGreaterThan(0)
    expect(screen.getByText(/60%/)).toBeInTheDocument()
  })

  it('triggers AI report generation', async () => {
    ;(adminReportsApi.getDetail as any).mockResolvedValue({ data: detail })
    ;(adminReportsApi.generateReport as any).mockResolvedValue({
      data: {
        summary: 'Resumen IA.',
        strengths: ['x'], weaknesses: ['y'],
        risk_level: 'bajo', risk_reason: 'ok', interventions: ['z'],
        generated_at: '2026-05-27T10:00:00Z',
        cached: false,
      },
    })
    render(wrap('/admin/students/u1'))
    await screen.findByText('Ana')
    fireEvent.click(screen.getByRole('button', { name: /Generar reporte/i }))
    await waitFor(() =>
      expect(screen.getByText('Resumen IA.')).toBeInTheDocument()
    )
  })

  it('test_print_button_invokes_window_print', async () => {
    ;(adminReportsApi.getDetail as any).mockResolvedValue({ data: detail })
    render(wrap('/admin/students/u1'))
    await screen.findByText('Ana')
    fireEvent.click(screen.getByRole('button', { name: /Descargar PDF/i }))
    await waitFor(() => expect(generateReportPDF).toHaveBeenCalled())
  })
})
