import { useState, useRef, useEffect, useCallback } from 'react'
import {
  Plus,
  MessageCircle,
  Trash2,
  Send,
  Sparkles,
  PanelLeftClose,
  PanelLeftOpen,
  AlertTriangle,
  RotateCcw,
  Square,
  Check,
  X,
  Search,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import EmptyState from '@/components/common/EmptyState'
import Skeleton from '@/components/common/Skeleton'
import ChatMessageComponent from '@/components/chat/ChatMessage'
import TypingIndicator from '@/components/chat/TypingIndicator'
import {
  useChatSessions,
  useChatMessages,
  useCreateSession,
  useDeleteSession,
  useSendMessage,
  useChatRemaining,
} from '@/hooks/useChat'
import { formatRelativeTime } from '@/lib/datetime'
import type { ChatMessage } from '@/types/chat'

/** Map a failed-send error to a clear, context-specific message for the student. */
function describeSendError(error: unknown): string {
  if (typeof navigator !== 'undefined' && navigator.onLine === false) {
    return 'Parece que no tienes conexión. Revisa tu internet e intenta de nuevo.'
  }
  const response = (error as { response?: { status?: number } })?.response
  const status = response?.status
  if (status === 429) {
    return 'Has alcanzado el límite de consultas por hora. Intenta más tarde.'
  }
  if (status === 503 || !response) {
    // 503, or no response at all (backend / Ollama unreachable).
    return 'El tutor no está disponible en este momento. Intenta de nuevo en unos segundos.'
  }
  return 'No se pudo enviar tu mensaje. Intenta de nuevo.'
}

export default function ChatPage() {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [input, setInput] = useState('')
  // Default closed on mobile (<lg) so chat area is visible on first paint.
  const [sidebarOpen, setSidebarOpen] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(min-width: 1024px)').matches
  )
  const [optimisticMessages, setOptimisticMessages] = useState<ChatMessage[]>([])
  // Failure message after a send fails (not a cancel); drives the inline retry banner.
  const [sendError, setSendError] = useState<string | null>(null)
  // Session pending a delete confirmation (inline, non-modal).
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<string | null>(null)
  // Sidebar conversation filter query.
  const [sessionQuery, setSessionQuery] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  // Controller for the in-flight send, so it can be cancelled.
  const abortRef = useRef<AbortController | null>(null)

  const { data: sessions = [], isLoading: loadingSessions } = useChatSessions()
  const { data: serverMessages = [], isLoading: loadingMessages } = useChatMessages(activeSessionId)
  const { data: remaining } = useChatRemaining()
  const createSession = useCreateSession()
  const deleteSession = useDeleteSession()
  const sendMessage = useSendMessage(activeSessionId)

  const messages = [...serverMessages, ...optimisticMessages]
  const limitReached = (remaining?.remaining ?? 1) <= 0
  const visibleSessions = sessionQuery.trim()
    ? sessions.filter((s) =>
        s.title.toLowerCase().includes(sessionQuery.trim().toLowerCase())
      )
    : sessions

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, sendMessage.isPending])

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current
    if (ta) {
      ta.style.height = 'auto'
      ta.style.height = `${Math.min(ta.scrollHeight, 150)}px`
    }
  }, [input])

  // Close the overlay drawer (<lg) on Escape for keyboard users.
  useEffect(() => {
    if (!sidebarOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (
        e.key === 'Escape' &&
        typeof window !== 'undefined' &&
        !window.matchMedia('(min-width: 1024px)').matches
      ) {
        setSidebarOpen(false)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [sidebarOpen])

  // Abort any in-flight request when the page unmounts.
  useEffect(() => () => abortRef.current?.abort(), [])

  const handleNewSession = useCallback(async () => {
    setConfirmingDeleteId(null)
    setSendError(null)
    const session = await createSession.mutateAsync()
    setActiveSessionId(session.id)
    setOptimisticMessages([])
    // Auto-close drawer on mobile so the chat surface is visible
    if (
      typeof window !== 'undefined' &&
      !window.matchMedia('(min-width: 1024px)').matches
    ) {
      setSidebarOpen(false)
    }
    textareaRef.current?.focus()
  }, [createSession])

  const handleSelectSession = useCallback((sessionId: string) => {
    setActiveSessionId(sessionId)
    setOptimisticMessages([])
    setConfirmingDeleteId(null)
    setSendError(null)
    // Auto-close drawer on mobile after selection
    if (
      typeof window !== 'undefined' &&
      !window.matchMedia('(min-width: 1024px)').matches
    ) {
      setSidebarOpen(false)
    }
  }, [])

  const handleConfirmDelete = useCallback(
    async (sessionId: string, e: React.MouseEvent) => {
      e.stopPropagation()
      setConfirmingDeleteId(null)
      try {
        await deleteSession.mutateAsync(sessionId)
        if (activeSessionId === sessionId) {
          setActiveSessionId(null)
          setOptimisticMessages([])
        }
      } catch {
        // Hook surfaces a toast; keep the session in the list so nothing is lost.
      }
    },
    [deleteSession, activeSessionId]
  )

  const handleSend = useCallback(async () => {
    const trimmed = input.trim()
    if (!trimmed || !activeSessionId || sendMessage.isPending) return

    setSendError(null)
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: trimmed,
      sources: null,
      created_at: new Date().toISOString(),
    }
    setOptimisticMessages([tempUserMsg])
    setInput('')

    const controller = new AbortController()
    abortRef.current = controller

    try {
      await sendMessage.mutateAsync({ content: trimmed, signal: controller.signal })
      setOptimisticMessages([])
    } catch (err) {
      // Never lose the student's question: drop the optimistic bubble, restore the text.
      setOptimisticMessages([])
      setInput(trimmed)
      // A user-initiated cancel is silent; a real failure offers an inline retry.
      if (!controller.signal.aborted) setSendError(describeSendError(err))
      textareaRef.current?.focus()
    } finally {
      if (abortRef.current === controller) abortRef.current = null
    }
  }, [input, activeSessionId, sendMessage])

  const handleCancel = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Ctrl/Cmd+K starts a new conversation from anywhere on the page.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        handleNewSession()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [handleNewSession])

  return (
    <div className="relative flex h-[calc(100dvh-4rem)] overflow-hidden">
      {/* Screen-reader status for async send state */}
      <p className="sr-only" role="status" aria-live="polite">
        {sendMessage.isPending ? 'El tutor está escribiendo una respuesta.' : ''}
      </p>

      {/* Mobile backdrop when sidebar is open (<lg only) */}
      {sidebarOpen && (
        <button
          type="button"
          aria-label="Cerrar historial"
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 top-16 z-30 bg-institutional-900/60 lg:hidden"
        />
      )}
      {/* Sessions sidebar — overlay drawer on mobile, in-flow on lg+ */}
      <aside
        aria-label="Historial de conversaciones"
        className={`${
          sidebarOpen
            ? 'translate-x-0 w-72 lg:w-72'
            : '-translate-x-full w-72 lg:w-0 lg:translate-x-0'
        } fixed lg:static inset-y-16 left-0 z-40 lg:z-auto lg:inset-auto transition-all duration-200 bg-card border-r border-border flex flex-col overflow-hidden shrink-0`}
      >
        <div className="p-3 border-b border-border">
          <Button
            onClick={handleNewSession}
            disabled={createSession.isPending}
            className="w-full justify-center gap-2"
            size="sm"
            title="Nueva conversación (Ctrl+K)"
          >
            <Plus className="w-4 h-4" />
            Nueva conversación
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loadingSessions ? (
            <div className="space-y-2 p-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} variant="rect" className="h-12 w-full" />
              ))}
            </div>
          ) : sessions.length === 0 ? (
            <EmptyState
              icon={MessageCircle}
              title="Sin conversaciones"
              description="Inicia tu primera conversación con el tutor IA."
              action={
                <Button onClick={handleNewSession} disabled={createSession.isPending}>
                  Nueva conversación
                </Button>
              }
              className="py-6"
            />
          ) : (
            <>
              {sessions.length > 5 && (
                <div className="px-3 py-2">
                  <div className="relative">
                    <Search
                      className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
                      aria-hidden="true"
                    />
                    <input
                      type="text"
                      value={sessionQuery}
                      onChange={(e) => setSessionQuery(e.target.value)}
                      placeholder="Buscar conversación..."
                      aria-label="Buscar conversación"
                      className="h-9 w-full rounded-lg border border-input bg-background pl-8 pr-3 text-sm
                                 placeholder:text-muted-foreground
                                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-primary"
                    />
                  </div>
                </div>
              )}
              {visibleSessions.length === 0 ? (
                <p className="px-3 py-6 text-center text-sm text-muted-foreground">
                  Sin resultados para esa búsqueda.
                </p>
              ) : (
                <ul className="p-2 space-y-0.5">
                  {visibleSessions.map((session) => {
                const isActive = activeSessionId === session.id
                const isConfirming = confirmingDeleteId === session.id
                const lastActive = formatRelativeTime(session.last_message_at)
                return (
                  <li key={session.id}>
                    <div
                      className={`group relative rounded-lg transition-colors ${
                        isActive ? 'bg-primary/10 text-primary' : 'text-foreground hover:bg-muted'
                      }`}
                    >
                      {isConfirming ? (
                        <div
                          role="group"
                          aria-label={`Confirmar eliminación de: ${session.title}`}
                          className="flex items-center gap-1 py-1.5 pl-3 pr-1"
                        >
                          <span className="flex-1 truncate text-xs text-muted-foreground">
                            ¿Eliminar conversación?
                          </span>
                          <button
                            type="button"
                            onClick={(e) => handleConfirmDelete(session.id, e)}
                            disabled={deleteSession.isPending}
                            aria-label={`Confirmar: eliminar ${session.title}`}
                            className="inline-flex items-center justify-center min-h-[40px] min-w-[40px]
                                       rounded-md text-destructive hover:bg-destructive/10
                                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring
                                       disabled:opacity-50 transition-colors"
                          >
                            <Check className="w-4 h-4" />
                          </button>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              setConfirmingDeleteId(null)
                            }}
                            aria-label="Cancelar eliminación"
                            className="inline-flex items-center justify-center min-h-[40px] min-w-[40px]
                                       rounded-md text-muted-foreground hover:text-foreground hover:bg-muted
                                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring
                                       transition-colors"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ) : (
                        <>
                          <button
                            type="button"
                            onClick={() => handleSelectSession(session.id)}
                            aria-current={isActive ? 'true' : undefined}
                            className="w-full text-left pl-3 pr-10 py-2.5 text-sm
                                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg"
                          >
                            <span className="truncate block">{session.title}</span>
                            {lastActive && (
                              <span className="mt-0.5 block text-xs text-muted-foreground">
                                {lastActive}
                              </span>
                            )}
                          </button>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              setConfirmingDeleteId(session.id)
                            }}
                            aria-label={`Eliminar conversación: ${session.title}`}
                            className="absolute right-0.5 top-1/2 -translate-y-1/2
                                       inline-flex items-center justify-center min-h-[40px] min-w-[40px]
                                       rounded-md text-muted-foreground opacity-0
                                       group-hover:opacity-100 focus:opacity-100 focus-visible:opacity-100
                                       hover:text-destructive hover:bg-destructive/10
                                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring
                                       transition-opacity"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </>
                      )}
                    </div>
                  </li>
                )
              })}
                </ul>
              )}
            </>
          )}
        </div>
      </aside>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border bg-card">
          <button
            type="button"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label={sidebarOpen ? 'Cerrar historial' : 'Abrir historial'}
            aria-expanded={sidebarOpen}
            className="inline-flex items-center justify-center min-h-[44px] min-w-[44px] -ml-2
                       text-muted-foreground hover:text-foreground rounded-lg transition-colors
                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {sidebarOpen ? (
              <PanelLeftClose className="w-5 h-5" />
            ) : (
              <PanelLeftOpen className="w-5 h-5" />
            )}
          </button>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary-500" aria-hidden="true" />
            <h1 className="text-lg font-semibold tracking-tight text-foreground">Tutor IA</h1>
          </div>
          {remaining && (
            <span
              className={`ml-auto text-xs tabular-nums whitespace-nowrap ${
                remaining.remaining <= 3 ? 'text-warning font-medium' : 'text-muted-foreground'
              }`}
              aria-label={`${remaining.remaining} de ${remaining.limit} consultas disponibles`}
            >
              <span className="sm:hidden">
                {remaining.remaining}/{remaining.limit}
              </span>
              <span className="hidden sm:inline">
                {remaining.remaining} de {remaining.limit} consultas disponibles
              </span>
            </span>
          )}
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          {!activeSessionId ? (
            <EmptyState
              icon={Sparkles}
              title="Tutor IA del Curso"
              description={
                'Pregúntame sobre cualquier tema del curso de Aplicaciones Móviles. Puedo ayudarte con Kotlin, Android Studio, layouts XML, Activities, APIs REST y más.'
              }
              action={
                <Button onClick={handleNewSession} disabled={createSession.isPending}>
                  <Plus className="w-4 h-4 mr-2" />
                  Iniciar conversación
                </Button>
              }
            />
          ) : loadingMessages ? (
            <div className="space-y-4 p-4" aria-busy="true">
              <Skeleton variant="rect" className="h-16 w-3/4" />
              <Skeleton variant="rect" className="h-20 w-2/3 ml-auto" />
              <Skeleton variant="rect" className="h-16 w-3/4" />
            </div>
          ) : messages.length === 0 ? (
            <EmptyState
              icon={MessageCircle}
              title="¿Sobre qué quieres aprender?"
              description={
                "Pregúntale al tutor sobre los temas del curso. Por ejemplo: '¿Qué es Jetpack Compose?'"
              }
            />
          ) : (
            <div className="max-w-3xl mx-auto">
              {messages.map((msg) => (
                <ChatMessageComponent key={msg.id} message={msg} />
              ))}
              {sendMessage.isPending && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input area */}
        {activeSessionId && (
          <div className="border-t border-border bg-card px-4 py-3">
            <div className="max-w-3xl mx-auto">
              {limitReached && (
                <div
                  role="alert"
                  className="flex items-center gap-2 text-sm text-warning bg-warning/10 border border-warning/30 rounded-lg px-3 py-2 mb-3"
                >
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>
                    Has alcanzado el límite de consultas por hora. Intenta de nuevo más tarde.
                  </span>
                </div>
              )}
              {sendError && !limitReached && (
                <div
                  role="alert"
                  className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2 mb-3"
                >
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span className="flex-1">{sendError}</span>
                  <button
                    type="button"
                    onClick={handleSend}
                    className="inline-flex items-center gap-1 font-medium text-destructive
                               hover:underline focus-visible:outline-none focus-visible:ring-2
                               focus-visible:ring-ring rounded px-1"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    Reintentar
                  </button>
                </div>
              )}
              <div className="flex items-end gap-2">
                <Textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => {
                    setInput(e.target.value)
                    if (sendError) setSendError(null)
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder="Escribe tu pregunta..."
                  rows={1}
                  maxLength={2000}
                  aria-label="Mensaje al tutor"
                  disabled={sendMessage.isPending || limitReached}
                  className="flex-1 min-h-[44px] !h-auto resize-none text-base sm:text-sm bg-muted/50"
                />
                {sendMessage.isPending ? (
                  <Button
                    onClick={handleCancel}
                    variant="outline"
                    size="icon"
                    aria-label="Detener generación"
                    className="shrink-0 h-11 w-11 rounded-md"
                  >
                    <Square className="w-4 h-4 fill-current" />
                  </Button>
                ) : (
                  <Button
                    onClick={handleSend}
                    disabled={!input.trim() || limitReached}
                    size="icon"
                    aria-label="Enviar mensaje"
                    className="shrink-0 h-11 w-11 rounded-md"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-2 text-center">
                Enter para enviar · Shift+Enter para nueva línea
                {input.length > 1800 && (
                  <span className="ml-2 tabular-nums">{input.length}/2000</span>
                )}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
