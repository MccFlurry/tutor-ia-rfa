import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import CohortReportModal from './CohortReportModal'
import { adminReportsApi } from '@/api/adminReports'

vi.mock('@/api/adminReports', () => ({
  adminReportsApi: {
    generateCohortReport: vi.fn(),
  },
}))

function wrap(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{ui}</QueryClientProvider>
}

const students = [
  { user_id: 'u1', full_name: 'Ana', email: 'a@x', level: 'beginner',
    entry_score: null, overall_progress_pct: 0, avg_quiz_score: null,
    avg_coding_score: null, last_activity_at: null, last_location: null,
    is_active: true },
  { user_id: 'u2', full_name: 'Bruno', email: 'b@x', level: 'intermediate',
    entry_score: null, overall_progress_pct: 0, avg_quiz_score: null,
    avg_coding_score: null, last_activity_at: null, last_location: null,
    is_active: true },
]

describe('CohortReportModal', () => {
  it('disables generate button until at least 2 selected', () => {
    render(wrap(<CohortReportModal students={students as any} onClose={() => {}} />))
    expect(screen.getByRole('button', { name: /Generar reporte/i })).toBeDisabled()
    fireEvent.click(screen.getByLabelText('Ana'))
    expect(screen.getByRole('button', { name: /Generar reporte/i })).toBeDisabled()
    fireEvent.click(screen.getByLabelText('Bruno'))
    expect(screen.getByRole('button', { name: /Generar reporte/i })).toBeEnabled()
  })

  it('renders narrative after API call', async () => {
    ;(adminReportsApi.generateCohortReport as any).mockResolvedValue({
      data: {
        narrative: 'Grupo desigual.',
        top_performers: ['Ana'],
        needs_support: ['Bruno'],
        common_gaps: [],
        recommendations: ['x'],
        generated_at: '2026-05-27T10:00:00Z',
        cached: false,
      },
    })
    render(wrap(<CohortReportModal students={students as any} onClose={() => {}} />))
    fireEvent.click(screen.getByLabelText('Ana'))
    fireEvent.click(screen.getByLabelText('Bruno'))
    fireEvent.click(screen.getByRole('button', { name: /Generar reporte/i }))
    await waitFor(() =>
      expect(screen.getByText('Grupo desigual.')).toBeInTheDocument()
    )
  })

  it('calls onClose when close button clicked', () => {
    const onClose = vi.fn()
    render(wrap(<CohortReportModal students={students as any} onClose={onClose} />))
    fireEvent.click(screen.getByRole('button', { name: /Cerrar/i }))
    expect(onClose).toHaveBeenCalled()
  })
})
