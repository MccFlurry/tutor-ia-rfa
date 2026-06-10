import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import DiagnosticChips from './DiagnosticChips'
import type { ModuleDiagnostic } from '@/types/companion'

function makeDiagnostic(over: Partial<ModuleDiagnostic> = {}): ModuleDiagnostic {
  return {
    weak: [{ topic_id: 12, title: 'Layouts', best_score: 45, attempts: 2 }],
    practice: [{ topic_id: 13, title: 'Intents', best_score: 70, attempts: 1 }],
    next_action: { kind: 'retry_quiz', label: 'Repasar «Layouts»', route: '/topics/12' },
    ...over,
  }
}

describe('<DiagnosticChips />', () => {
  it('renders weak and practice chips linking to topics', () => {
    render(
      <MemoryRouter>
        <DiagnosticChips diagnostic={makeDiagnostic()} />
      </MemoryRouter>
    )
    const weak = screen.getByRole('link', { name: /Repasar: Layouts/ })
    expect(weak).toHaveAttribute('href', '/topics/12')
    const practice = screen.getByRole('link', { name: /Afianzar: Intents/ })
    expect(practice).toHaveAttribute('href', '/topics/13')
  })

  it('renders nothing when there is no diagnostic content', () => {
    const { container } = render(
      <MemoryRouter>
        <DiagnosticChips diagnostic={makeDiagnostic({ weak: [], practice: [] })} />
      </MemoryRouter>
    )
    expect(container).toBeEmptyDOMElement()
  })
})
