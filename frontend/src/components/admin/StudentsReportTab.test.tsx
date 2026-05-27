import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, useNavigate } from 'react-router-dom'
import StudentsReportTab from './StudentsReportTab'
import { adminReportsApi } from '@/api/adminReports'

vi.mock('@/api/adminReports', () => ({
  adminReportsApi: {
    listStudents: vi.fn(),
    generateCohortReport: vi.fn(),
  },
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: vi.fn() }
})

function wrap(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={client}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

const rows = [
  {
    user_id: 'u1', full_name: 'Ana', email: 'a@x', level: 'beginner',
    entry_score: 50, overall_progress_pct: 60, avg_quiz_score: 0.8,
    avg_coding_score: 70, last_activity_at: null, last_location: null,
    is_active: true,
  },
  {
    user_id: 'u2', full_name: 'Bruno', email: 'b@x', level: 'intermediate',
    entry_score: 70, overall_progress_pct: 20, avg_quiz_score: 0.4,
    avg_coding_score: 50, last_activity_at: null, last_location: null,
    is_active: true,
  },
]

describe('StudentsReportTab', () => {
  it('renders rows from the API', async () => {
    ;(adminReportsApi.listStudents as any).mockResolvedValue({ data: rows })
    render(wrap(<StudentsReportTab />))
    expect(await screen.findByText('Ana')).toBeInTheDocument()
    expect(screen.getByText('Bruno')).toBeInTheDocument()
  })

  it('navigates to detail on row click', async () => {
    const navigate = vi.fn()
    ;(useNavigate as any).mockReturnValue(navigate)
    ;(adminReportsApi.listStudents as any).mockResolvedValue({ data: rows })

    render(wrap(<StudentsReportTab />))
    const row = await screen.findByText('Ana')
    fireEvent.click(row.closest('tr')!)
    expect(navigate).toHaveBeenCalledWith('/admin/students/u1')
  })

  it('filters by level', async () => {
    ;(adminReportsApi.listStudents as any).mockResolvedValue({ data: rows })
    render(wrap(<StudentsReportTab />))
    await screen.findByText('Ana')
    fireEvent.change(screen.getByLabelText(/Filtrar por nivel/i), {
      target: { value: 'intermediate' },
    })
    expect(screen.queryByText('Ana')).not.toBeInTheDocument()
    expect(screen.getByText('Bruno')).toBeInTheDocument()
  })

  it('sorts by progress descending on column click', async () => {
    ;(adminReportsApi.listStudents as any).mockResolvedValue({ data: rows })
    render(wrap(<StudentsReportTab />))
    await screen.findByText('Ana')
    const progressHeader = screen.getByRole('button', { name: /Progreso/i })
    fireEvent.click(progressHeader)
    const cells = screen.getAllByRole('row').slice(1).map(r => r.textContent || '')
    expect(cells[0].startsWith('Ana')).toBe(true)
  })
})
