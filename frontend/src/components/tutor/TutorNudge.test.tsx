import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import TutorNudge from './TutorNudge'
import type { Nudge } from '@/types/tutor'

function renderNudge(over: Partial<Nudge> = {}) {
  const nudge: Nudge = {
    id: 'welcome_start', tone: 'encourage', icon: 'rocket',
    title: '¡Bienvenido!', message: 'Empieza con el Módulo 1.',
    cta_label: 'Empezar', cta_route: '/modules', ...over,
  }
  return render(
    <MemoryRouter>
      <TutorNudge nudge={nudge} />
    </MemoryRouter>
  )
}

describe('<TutorNudge />', () => {
  it('renders title and message', () => {
    renderNudge()
    expect(screen.getByText('¡Bienvenido!')).toBeInTheDocument()
    expect(screen.getByText('Empieza con el Módulo 1.')).toBeInTheDocument()
  })

  it('renders CTA link when cta_route present', () => {
    renderNudge()
    const link = screen.getByRole('link', { name: 'Empezar' })
    expect(link).toHaveAttribute('href', '/modules')
  })

  it('omits CTA when no cta_route', () => {
    renderNudge({ cta_label: null, cta_route: null })
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })
})
