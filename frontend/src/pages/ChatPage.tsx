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
import type { ChatMessage } from '@/types/chat'

export default function ChatPage() {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [input, setInput] = useState('')
  // Default closed on mobile (<lg) so chat area is visible on first paint.
  const [sidebarOpen, setSidebarOpen] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(min-width: 1024px)').matches
  )
  const [optimisticMessages, setOptimisticMessages] = useState<ChatMessage[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const { data: sessions = [], isLoading: loadingSessions } = useChatSessions()
  const { data: serverMessages = [], isLoading: loadingMessages } = useChatMessages(activeSessionId)
  const { data: remaining } = useChatRemaining()
  const createSession = useCreateSession()
  const deleteSession = useDeleteSession()
  const sendMessage = useSendMessage(activeSessionId)

  const messages = [...serverMessages, ...optimisticMessages]

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

  const handleNewSession = useCallback(async () => {
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

  const handleDeleteSession = useCallback(
    async (sessionId: string, e: React.MouseEvent) => {
      e.stopPropagation()
      await deleteSession.mutateAsync(sessionId)
      if (activeSessionId === sessionId) {
        setActiveSessionId(null)
        setOptimisticMessages([])
      }
    },
    [deleteSession, activeSessionId]
  )

  const handleSend = useCallback(async () => {
    const trimmed = input.trim()
    if (!trimmed || !activeSessionId || sendMessage.isPending) return

    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: trimmed,
      sources: null,
      created_at: new Date().toISOString(),
    }
    setOptimisticMessages([tempUserMsg])
    setInput('')

    try {
      await sendMessage.mutateAsync(trimmed)
      setOptimisticMessages([])
    } catch {
      setOptimisticMessages([])
    }
  }, [input, activeSessionId, sendMessage])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="relative flex h-[calc(100dvh-4rem)] overflow-hidden">
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
                <button
                  onClick={handleNewSession}
                  disabled={createSession.isPending}
                  className="inline-flex items-center justify-center min-h-[44px] px-6 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-colors text-sm disabled:opacity-50"
                >
                  Nueva conversación
                </button>
              }
              className="py-6"
            />
          ) : (
            <ul className="p-2 space-y-0.5">
              {sessions.map((session) => {
                const isActive = activeSessionId === session.id
                return (
                  <li key={session.id}>
                    <div
                      className={`group relative rounded-lg transition-colors ${
                        isActive ? 'bg-primary/10 text-primary' : 'text-foreground hover:bg-muted'
                      }`}
                    >
                      <button
                        type="button"
                        onClick={() => {
                          setActiveSessionId(session.id)
                          setOptimisticMessages([])
                          // Auto-close drawer on mobile after selection
                          if (
                            typeof window !== 'undefined' &&
                            !window.matchMedia('(min-width: 1024px)').matches
                          ) {
                            setSidebarOpen(false)
                          }
                        }}
                        aria-current={isActive ? 'true' : undefined}
                        className="w-full text-left pl-3 pr-10 py-2.5 text-sm
                                   focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg"
                      >
                        <span className="truncate block">{session.title}</span>
                      </button>
                      <button
                        type="button"
                        onClick={(e) => handleDeleteSession(session.id, e)}
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
                    </div>
                  </li>
                )
              })}
            </ul>
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
            <h1 className="font-semibold text-foreground">Tutor IA</h1>
          </div>
          {remaining && (
            <span
              className="ml-auto text-xs text-muted-foreground tabular-nums whitespace-nowrap"
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
              {remaining && remaining.remaining <= 0 && (
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
              <div className="flex items-end gap-2">
                <Textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Escribe tu pregunta..."
                  rows={1}
                  aria-label="Mensaje al tutor"
                  disabled={sendMessage.isPending || (remaining?.remaining ?? 1) <= 0}
                  className="flex-1 min-h-[44px] !h-auto resize-none text-base sm:text-sm bg-muted/50"
                />
                <Button
                  onClick={handleSend}
                  disabled={
                    !input.trim() ||
                    sendMessage.isPending ||
                    (remaining?.remaining ?? 1) <= 0
                  }
                  size="icon"
                  aria-label="Enviar mensaje"
                  className="shrink-0 h-11 w-11 rounded-xl"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-2 text-center">
                Enter para enviar · Shift+Enter para nueva línea
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
