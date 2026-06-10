import { useState, useEffect, useRef, useCallback } from 'react'
import { useLocation } from 'react-router-dom'
import { Sparkles, X, Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import ChatMessageComponent from '@/components/chat/ChatMessage'
import TypingIndicator from '@/components/chat/TypingIndicator'
import {
  useCreateSession,
  useChatMessages,
  useSendMessage,
  useChatRemaining,
} from '@/hooks/useChat'
import { useCompanion } from '@/hooks/useCompanion'
import type { ChatMessage } from '@/types/chat'

const GREETING_SESSION_KEY = 'tutor_greeting_shown'
const GREETING_AUTOHIDE_MS = 12_000

export default function FloatingTutor() {
  const [open, setOpen] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [input, setInput] = useState('')
  const [optimistic, setOptimistic] = useState<ChatMessage[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const location = useLocation()

  const createSession = useCreateSession()
  const { data: serverMessages = [] } = useChatMessages(sessionId)
  const { data: remaining } = useChatRemaining()
  const sendMessage = useSendMessage(sessionId)

  const [showGreeting, setShowGreeting] = useState(false)
  const { data: companion } = useCompanion()

  // Burbuja preview (Fase 5): saludo contextual, 1 vez por sesión de navegador.
  // Decisión de mostrar separada del timer: idempotente bajo StrictMode
  // (el doble-invoke de dev consumiría el flag sin re-armar el auto-ocultado).
  useEffect(() => {
    if (open || !companion?.greeting) return
    if (sessionStorage.getItem(GREETING_SESSION_KEY)) return
    sessionStorage.setItem(GREETING_SESSION_KEY, '1')
    setShowGreeting(true)
  }, [companion?.greeting, open])

  useEffect(() => {
    if (!showGreeting) return
    const timer = setTimeout(() => setShowGreeting(false), GREETING_AUTOHIDE_MS)
    return () => clearTimeout(timer)
  }, [showGreeting])

  useEffect(() => {
    if (!showGreeting) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setShowGreeting(false)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [showGreeting])

  const messages = [...serverMessages, ...optimistic]

  const handleOpen = useCallback(async () => {
    setShowGreeting(false)
    setOpen(true)
    if (!input && location.pathname.startsWith('/topics/')) {
      setInput('Sobre el tema actual, ')
    }
    if (!sessionId && !createSession.isPending) {
      try {
        const s = await createSession.mutateAsync()
        setSessionId(s.id)
      } catch {
        // si falla la creación, el panel sigue abierto; el usuario puede reintentar
      }
    }
  }, [sessionId, createSession, input, location.pathname])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open])

  // Move focus into the panel textarea when the panel opens and the session is ready.
  useEffect(() => {
    if (!open) return
    // Use a minimal delay so the panel has painted before we focus.
    const timer = setTimeout(() => {
      textareaRef.current?.focus()
    }, 50)
    return () => clearTimeout(timer)
  }, [open, sessionId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  const handleSend = useCallback(async () => {
    const trimmed = input.trim()
    if (!trimmed || !sessionId || sendMessage.isPending) return
    const temp: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: trimmed,
      sources: null,
      created_at: new Date().toISOString(),
    }
    setOptimistic([temp])
    setInput('')
    try {
      await sendMessage.mutateAsync(trimmed)
      setOptimistic([])
    } catch {
      // Restore the question so the student doesn't lose their work.
      setOptimistic([])
      setInput(trimmed)
      textareaRef.current?.focus()
    }
  }, [input, sessionId, sendMessage])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const rateLimited = (remaining?.remaining ?? 1) <= 0

  return (
    <>
      {!open && (
        <>
          {showGreeting && companion?.greeting && (
            <div
              role="status"
              className="fixed bottom-20 right-4 z-40 max-w-[280px] rounded-xl border border-border
                         bg-card p-3 shadow-xl
                         motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2"
            >
              <p className="text-sm text-foreground">{companion.greeting}</p>
              <div className="mt-2 flex items-center gap-2">
                <Button size="sm" onClick={handleOpen}>
                  Abrir tutor
                </Button>
                <button
                  type="button"
                  onClick={() => setShowGreeting(false)}
                  aria-label="Cerrar saludo del tutor"
                  className="inline-flex items-center justify-center min-h-[44px] min-w-[44px]
                             rounded-lg text-muted-foreground hover:text-foreground transition-colors
                             focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
          <button
            type="button"
            onClick={handleOpen}
            aria-label="Abrir tutor IA"
            className="fixed bottom-4 right-4 z-40 inline-flex items-center justify-center
                       h-14 w-14 rounded-full bg-primary text-primary-foreground shadow-lg
                       hover:bg-primary/90 transition-colors
                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Sparkles className="h-6 w-6" aria-hidden="true" />
          </button>
        </>
      )}

      {open && (
        <div
          role="dialog"
          aria-label="Tutor IA"
          aria-modal="false"
          className="fixed z-50 flex flex-col bg-card border border-border shadow-xl
                     inset-0 h-[100dvh] w-full
                     sm:inset-auto sm:bottom-4 sm:right-4 sm:h-[600px] sm:w-96 sm:rounded-xl"
        >
          <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
            <Sparkles className="h-5 w-5 text-primary" aria-hidden="true" />
            <span className="font-semibold text-foreground">Tutor IA</span>
            {remaining && (
              <span
                className={`ml-auto text-xs tabular-nums ${
                  remaining.remaining <= 3 ? 'text-warning font-medium' : 'text-muted-foreground'
                }`}
                aria-label={`${remaining.remaining} de ${remaining.limit} consultas disponibles`}
              >
                {remaining.remaining}/{remaining.limit}
              </span>
            )}
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Cerrar tutor"
              className="ml-2 inline-flex items-center justify-center min-h-[44px] min-w-[44px]
                         rounded-lg text-muted-foreground hover:text-foreground transition-colors
                         focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-3 py-3">
            {messages.length === 0 ? (
              <p className="text-sm text-muted-foreground px-1">
                Pregúntame sobre el curso de Aplicaciones Móviles: Kotlin, layouts, Activities, APIs REST y más.
              </p>
            ) : (
              <>
                {messages.map((msg) => (
                  <ChatMessageComponent key={msg.id} message={msg} />
                ))}
                {sendMessage.isPending && <TypingIndicator />}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          <p className="sr-only" aria-live="polite" aria-atomic="true">
            {!sendMessage.isPending
              ? [...messages].reverse().find((m) => m.role === 'assistant')?.content ?? ''
              : ''}
          </p>

          <div className="border-t border-border p-2">
            {rateLimited && (
              <p role="alert" className="text-xs text-warning px-1 pb-2">
                Has alcanzado el límite de consultas por hora. Intenta más tarde.
              </p>
            )}
            <div className="flex items-end gap-2">
              <Textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Escribe tu pregunta..."
                rows={1}
                aria-label="Mensaje al tutor"
                disabled={sendMessage.isPending || rateLimited}
                className="flex-1 min-h-[44px] !h-auto resize-none text-base sm:text-sm bg-muted/50"
              />
              <Button
                onClick={handleSend}
                disabled={!input.trim() || sendMessage.isPending || rateLimited}
                size="icon"
                aria-label="Enviar mensaje"
                className="shrink-0 h-11 w-11 rounded-xl"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
