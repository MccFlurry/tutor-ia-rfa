import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Inbox } from 'lucide-react'
import EmptyState from './EmptyState'

describe('<EmptyState />', () => {
  it('renders title (required)', () => {
    render(<EmptyState title="Sin datos" />)
    expect(screen.getByText('Sin datos')).toBeInTheDocument()
  })

  it('renders description + action when provided', () => {
    render(
      <EmptyState
        title="Sin datos"
        description="Aún no hay nada"
        action={<button>Recargar</button>}
      />
    )
    expect(screen.getByText('Aún no hay nada')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Recargar' })).toBeInTheDocument()
  })

  it('renders icon when no illustration', () => {
    const { container } = render(<EmptyState title="x" icon={Inbox} />)
    // Lucide renders an SVG element
    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('prefers illustration over icon when both provided', () => {
    render(
      <EmptyState
        title="x"
        icon={Inbox}
        illustration="/empty.svg"
        illustrationAlt="Vacío"
      />
    )
    expect(screen.getByAltText('Vacío')).toBeInTheDocument()
  })

  it('renders ReactNode illustration as-is', () => {
    render(
      <EmptyState
        title="x"
        illustration={<div data-testid="custom-illust">Custom</div>}
      />
    )
    expect(screen.getByTestId('custom-illust')).toBeInTheDocument()
  })
})
