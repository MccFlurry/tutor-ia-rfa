import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import FloatingTutor from './FloatingTutor'

vi.mock('@/hooks/useChat', () => ({
  useCreateSession: () => ({ mutateAsync: vi.fn().mockResolvedValue({ id: 's1' }), isPending: false }),
  useChatMessages: () => ({ data: [] }),
  useSendMessage: () => ({ mutateAsync: vi.fn().mockResolvedValue({}), isPending: false }),
  useChatRemaining: () => ({ data: { remaining: 20, limit: 20 } }),
}))

let companionData: import('@/types/companion').CompanionResponse | undefined

vi.mock('@/hooks/useCompanion', () => ({
  useCompanion: () => ({ data: companionData }),
}))

function renderTutor() {
  return render(
    <MemoryRouter>
      <FloatingTutor />
    </MemoryRouter>
  )
}

describe('<FloatingTutor />', () => {
  beforeEach(() => {
    sessionStorage.clear()
    companionData = undefined
  })

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

describe('FloatingTutor greeting bubble', () => {
  beforeEach(() => {
    sessionStorage.clear()
    companionData = {
      needs_assessment: false,
      position: {
        module_id: 3, module_title: 'Interfaces de Usuario', icon_name: null,
        color_hex: null, progress_pct: 60, topics_done: 3, topics_total: 5,
        course_completed: false,
      },
      greeting: 'Estás en «Interfaces de Usuario» — 60% completado.',
      diagnostic: null,
      resources: [],
    }
  })

  afterEach(() => {
    companionData = undefined
  })

  it('shows the greeting bubble once per session', () => {
    const { unmount } = renderTutor()
    expect(screen.getByRole('status')).toHaveTextContent('Interfaces de Usuario')
    unmount()
    renderTutor()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('close button hides the bubble', async () => {
    renderTutor()
    await userEvent.click(screen.getByRole('button', { name: 'Cerrar saludo del tutor' }))
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('does not show the bubble when needs_assessment', () => {
    companionData = { ...companionData!, needs_assessment: true }
    renderTutor()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('does not show the bubble without a student position', () => {
    companionData = { ...companionData!, position: null }
    renderTutor()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
