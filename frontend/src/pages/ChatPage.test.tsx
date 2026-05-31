import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

// Mutable mock handles, shared with the hoisted vi.mock below.
const h = vi.hoisted(() => ({
  sessions: [] as Array<{ id: string; title: string; created_at: string; last_message_at: string }>,
  sendPending: false,
  sendMutate: null as unknown as ReturnType<typeof vi.fn>,
  deleteMutate: null as unknown as ReturnType<typeof vi.fn>,
  createMutate: null as unknown as ReturnType<typeof vi.fn>,
}))

vi.mock('@/hooks/useChat', () => ({
  useChatSessions: () => ({ data: h.sessions, isLoading: false }),
  useChatMessages: () => ({ data: [], isLoading: false }),
  useChatRemaining: () => ({ data: { remaining: 20, limit: 20 } }),
  useCreateSession: () => ({ mutateAsync: h.createMutate, isPending: false }),
  useDeleteSession: () => ({ mutateAsync: h.deleteMutate, isPending: false }),
  useSendMessage: () => ({ mutateAsync: h.sendMutate, isPending: h.sendPending }),
}))

import ChatPage from './ChatPage'

const SESSION = { id: 's1', title: 'Conversación 1', created_at: '', last_message_at: '' }

beforeEach(() => {
  h.sessions = [SESSION]
  h.sendPending = false
  h.sendMutate = vi.fn().mockResolvedValue({})
  h.deleteMutate = vi.fn().mockResolvedValue('s1')
  h.createMutate = vi.fn().mockResolvedValue({ id: 's1' })
  // jsdom lacks these; ChatPage uses both.
  window.matchMedia = vi.fn().mockReturnValue({
    matches: false,
    media: '',
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }) as unknown as typeof window.matchMedia
  Element.prototype.scrollIntoView = vi.fn()
})

function selectSession() {
  render(<ChatPage />)
  fireEvent.click(screen.getByRole('button', { name: 'Conversación 1' }))
}

describe('<ChatPage /> resilience (Phase 1 harden)', () => {
  it('restores the typed question and shows a retry banner when a send fails', async () => {
    h.sendMutate = vi.fn().mockRejectedValue(new Error('503 Ollama down'))
    selectSession()

    const textarea = screen.getByLabelText('Mensaje al tutor') as HTMLTextAreaElement
    fireEvent.change(textarea, { target: { value: '¿Qué es Kotlin?' } })
    fireEvent.click(screen.getByRole('button', { name: 'Enviar mensaje' }))

    // The question is never lost: text returns to the input.
    await waitFor(() => expect(textarea.value).toBe('¿Qué es Kotlin?'))
    // And an in-context retry is offered.
    expect(screen.getByRole('button', { name: /Reintentar/ })).toBeInTheDocument()
    expect(h.sendMutate).toHaveBeenCalledTimes(1)
  })

  it('does not delete a conversation until the inline confirm is accepted', async () => {
    selectSession()

    fireEvent.click(screen.getByRole('button', { name: 'Eliminar conversación: Conversación 1' }))
    // First click only arms the confirm; nothing deleted yet.
    expect(h.deleteMutate).not.toHaveBeenCalled()
    expect(screen.getByText('¿Eliminar conversación?')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Confirmar: eliminar Conversación 1' }))
    await waitFor(() => expect(h.deleteMutate).toHaveBeenCalledWith('s1'))
  })

  it('offers a cancel (Stop) control while a response is in flight', () => {
    h.sendPending = true
    selectSession()

    expect(screen.getByRole('button', { name: 'Detener generación' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Enviar mensaje' })).not.toBeInTheDocument()
  })

  it('shows a tutor-unavailable message when the request has no response (503/Ollama down)', async () => {
    h.sendMutate = vi.fn().mockRejectedValue(new Error('network down'))
    selectSession()

    const textarea = screen.getByLabelText('Mensaje al tutor') as HTMLTextAreaElement
    fireEvent.change(textarea, { target: { value: 'hola' } })
    fireEvent.click(screen.getByRole('button', { name: 'Enviar mensaje' }))

    expect(await screen.findByText(/El tutor no está disponible/)).toBeInTheDocument()
  })

  it('starts a new conversation on Ctrl+K', async () => {
    render(<ChatPage />)
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
    await waitFor(() => expect(h.createMutate).toHaveBeenCalled())
  })

  it('filters the session list via the search box (shown only with several sessions)', () => {
    h.sessions = [
      { id: 'a', title: 'Kotlin básico', created_at: '', last_message_at: '' },
      { id: 'b', title: 'Layouts XML', created_at: '', last_message_at: '' },
      { id: 'c', title: 'Activities', created_at: '', last_message_at: '' },
      { id: 'd', title: 'APIs REST', created_at: '', last_message_at: '' },
      { id: 'e', title: 'Jetpack Compose', created_at: '', last_message_at: '' },
      { id: 'f', title: 'Room database', created_at: '', last_message_at: '' },
    ]
    render(<ChatPage />)

    fireEvent.change(screen.getByLabelText('Buscar conversación'), {
      target: { value: 'kotlin' },
    })
    expect(screen.getByText('Kotlin básico')).toBeInTheDocument()
    expect(screen.queryByText('Layouts XML')).not.toBeInTheDocument()
  })
})
