import { describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import FloatingTutor from './FloatingTutor'

vi.mock('@/hooks/useChat', () => ({
  useCreateSession: () => ({ mutateAsync: vi.fn().mockResolvedValue({ id: 's1' }), isPending: false }),
  useChatMessages: () => ({ data: [] }),
  useSendMessage: () => ({ mutateAsync: vi.fn().mockResolvedValue({}), isPending: false }),
  useChatRemaining: () => ({ data: { remaining: 20, limit: 20 } }),
}))

function renderTutor() {
  return render(
    <MemoryRouter>
      <FloatingTutor />
    </MemoryRouter>
  )
}

describe('<FloatingTutor />', () => {
  it('renders the toggle button, panel closed by default', () => {
    renderTutor()
    expect(screen.getByRole('button', { name: 'Abrir tutor IA' })).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('opens the panel on click', async () => {
    renderTutor()
    fireEvent.click(screen.getByRole('button', { name: 'Abrir tutor IA' }))
    expect(await screen.findByRole('dialog', { name: 'Tutor IA' })).toBeInTheDocument()
  })

  it('closes the panel with the close button', async () => {
    renderTutor()
    fireEvent.click(screen.getByRole('button', { name: 'Abrir tutor IA' }))
    await screen.findByRole('dialog', { name: 'Tutor IA' })
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar tutor' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
