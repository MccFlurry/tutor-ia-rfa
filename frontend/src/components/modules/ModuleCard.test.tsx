import { describe, expect, it } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import ModuleCard from './ModuleCard'
import type { Module } from '@/types/module'

function baseModule(overrides: Partial<Module> = {}): Module {
  return {
    id: 1,
    title: 'Fundamentos',
    description: 'Introducción',
    order_index: 1,
    icon_name: 'book',
    color_hex: '#3b82f6',
    total_topics: 4,
    completed_topics: 2,
    progress_pct: 50,
    is_locked: false,
    ...overrides,
  }
}

function renderWithRouter(ui: React.ReactNode, initialEntry = '/modules') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/modules" element={ui} />
        <Route path="/modules/:id" element={<div data-testid="detail-page" />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('<ModuleCard />', () => {
  it('renders title, description, and progress', () => {
    renderWithRouter(<ModuleCard module={baseModule()} />)
    expect(screen.getByText('Fundamentos')).toBeInTheDocument()
    expect(screen.getByText('Introducción')).toBeInTheDocument()
    expect(screen.getByText('2 de 4 temas')).toBeInTheDocument()
    expect(screen.getByText('50%')).toBeInTheDocument()
  })

  it('exposes button role and navigates on Enter when unlocked', async () => {
    const user = userEvent.setup()
    renderWithRouter(<ModuleCard module={baseModule()} />)
    const card = screen.getByRole('button', { name: /Fundamentos/ })
    expect(card).toHaveAttribute('tabindex', '0')
    card.focus()
    await user.keyboard('{Enter}')
    expect(screen.getByTestId('detail-page')).toBeInTheDocument()
  })

  it('locked module is non-interactive', () => {
    renderWithRouter(
      <ModuleCard module={baseModule({ is_locked: true, progress_pct: 0 })} />
    )
    const card = screen.getByLabelText(/Bloqueado/)
    expect(card).toHaveAttribute('aria-disabled', 'true')
    expect(card).toHaveAttribute('tabindex', '-1')
    // Click should not navigate
    fireEvent.click(card)
    expect(screen.queryByTestId('detail-page')).not.toBeInTheDocument()
  })

  it('shows "Completado" badge at 100%', () => {
    renderWithRouter(
      <ModuleCard module={baseModule({ progress_pct: 100, completed_topics: 4 })} />
    )
    expect(screen.getByText('Completado')).toBeInTheDocument()
  })

  it('shows "No iniciado" badge at 0%', () => {
    renderWithRouter(
      <ModuleCard module={baseModule({ progress_pct: 0, completed_topics: 0 })} />
    )
    expect(screen.getByText('No iniciado')).toBeInTheDocument()
  })
})
