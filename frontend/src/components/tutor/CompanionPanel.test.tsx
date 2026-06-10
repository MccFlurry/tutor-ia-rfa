import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import CompanionPanel from './CompanionPanel'
import type { CompanionResponse } from '@/types/companion'

function makeData(over: Partial<CompanionResponse> = {}): CompanionResponse {
  return {
    needs_assessment: false,
    position: {
      module_id: 3, module_title: 'Interfaces de Usuario', icon_name: null,
      color_hex: '#3b82f6', progress_pct: 60, topics_done: 3, topics_total: 5,
      course_completed: false,
    },
    greeting: 'Estás en «Interfaces de Usuario» — 60% completado.',
    diagnostic: {
      weak: [{ topic_id: 12, title: 'Layouts', best_score: 45, attempts: 2 }],
      practice: [{ topic_id: 13, title: 'Intents', best_score: 70, attempts: 1 }],
      next_action: { kind: 'retry_quiz', label: 'Repasar «Layouts»', route: '/topics/12' },
    },
    resources: [
      {
        id: 1, module_id: 3, topic_id: null, kind: 'video',
        title: 'Curso de Layouts', url: 'https://example.com', author: null,
        description: null, order_index: 0, is_active: true,
      },
    ],
    ...over,
  }
}

function renderPanel(data = makeData()) {
  return render(
    <MemoryRouter>
      <CompanionPanel data={data} />
    </MemoryRouter>
  )
}

describe('<CompanionPanel />', () => {
  it('renders current module, greeting and progress', () => {
    renderPanel()
    expect(screen.getByText('Interfaces de Usuario')).toBeInTheDocument()
    expect(screen.getByText(/60% completado/)).toBeInTheDocument()
    expect(screen.getByText(/3 de 5 temas/)).toBeInTheDocument()
  })

  it('renders next action CTA', () => {
    renderPanel()
    expect(screen.getByRole('button', { name: /Repasar «Layouts»/ })).toBeInTheDocument()
  })

  it('renders diagnostic chips and module resources', () => {
    renderPanel()
    expect(screen.getByRole('link', { name: /Repasar: Layouts/ })).toBeInTheDocument()
    expect(screen.getByText('Curso de Layouts')).toBeInTheDocument()
  })

  it('renders nothing without position or diagnostic', () => {
    const { container } = renderPanel(makeData({ position: null, diagnostic: null }))
    expect(container).toBeEmptyDOMElement()
  })
})
