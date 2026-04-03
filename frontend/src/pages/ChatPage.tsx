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
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [optimisticMessages, setOptimisticMessages] = useState<ChatMessage[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Data hooks
  const { data: sessions = [], isLoading: loadingSessions } = useChatSessions()
  const { data: serverMessages = [], isLoading: loadingMessages } = useChatMessages(activeSessionId)
  const { data: remaining } = useChatRemaining()
  const createSession = useCreateSession()
  const deleteSession = useDeleteSession()
  const sendMessage = useSendMessage(activeSessionId)

  // Combine server messages with optimistic ones
  const messages = [...serverMessages, ...optimisticMessages]

  // Auto-scroll to bottom when messages change
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

  // Handle new session creation
  const handleNewSession = useCallback(async () => {
    const session = await createSession.mutateAsync()
    setActiveSessionId(session.id)
    setOptimisticMessages([])
    textareaRef.current?.focus()
  }, [createSession])

  // Handle session deletion
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

  // Handle send message
  const handleSend = useCallback(async () => {
    const trimmed = input.trim()
    if (!trimmed || !activeSessionId || sendMessage.isPending) return

    // Add optimistic user message
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
      // Server refetch will replace optimistic messages
      setOptimisticMessages([])
    } catch {
      // Keep optimistic message to show what was sent
      setOptimisticMessages([])
    }
  }, [input, activeSessionId, sendMessage])

  // Handle key press (Enter to send, Shift+Enter for new line)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* Sessions sidebar */}
      <aside
        className={`${
          sidebarOpen ? 'w-72' : 'w-0'
        } transition-all duration-200 bg-white border-r border-gray-200 flex flex-col overflow-hidden shrink-0`}
      >
        {/* Sidebar header */}
        <div className="p-3 border-b border-gray-100">
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

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto">
          {loadingSessions ? (
            <div className="px-3 py-4 space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 bg-gray-100 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : sessions.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-gray-400">
              <MessageCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>Sin conversaciones aún</p>
            </div>
          ) : (
            <div className="p-2 space-y-0.5">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  role="button"
                  tabIndex={0}
                  onClick={() => {
                    setActiveSessionId(session.id)
                    setOptimisticMessages([])
                  }}
                  className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors group flex items-center justify-between gap-2 cursor-pointer ${
                    activeSessionId === session.id
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <span className="truncate flex-1">{session.title}</span>
                  <button
                    onClick={(e) => handleDeleteSession(session.id, e)}
                    className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all shrink-0"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </aside>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 bg-white">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            {sidebarOpen ? (
              <PanelLeftClose className="w-5 h-5" />
            ) : (
              <PanelLeftOpen className="w-5 h-5" />
            )}
          </button>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary-500" />
            <h1 className="font-semibold text-gray-900">Tutor IA</h1>
          </div>
          {remaining && (
            <span className="ml-auto text-xs text-gray-400">
              {remaining.remaining} de {remaining.limit} consultas disponibles
            </span>
          )}
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          {!activeSessionId ? (
            // No session selected
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
                <Sparkles className="w-8 h-8 text-primary-500" />
              </div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Tutor IA del Curso
              </h2>
              <p className="text-sm text-gray-500 max-w-md mb-6">
                Pregúntame sobre cualquier tema del curso de Aplicaciones Móviles.
                Puedo ayudarte con Kotlin, Android Studio, layouts XML, Activities,
                APIs REST y más.
              </p>
              <Button onClick={handleNewSession} disabled={createSession.isPending}>
                <Plus className="w-4 h-4 mr-2" />
                Iniciar conversación
              </Button>
            </div>
          ) : loadingMessages ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className={`flex gap-3 ${i % 2 === 0 ? 'flex-row-reverse' : ''}`}
                >
                  <div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse shrink-0" />
                  <div className="h-16 bg-gray-100 rounded-2xl animate-pulse w-2/3" />
                </div>
              ))}
            </div>
          ) : messages.length === 0 ? (
            // Empty session
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-12 h-12 bg-primary-50 rounded-full flex items-center justify-center mb-3">
                <MessageCircle className="w-6 h-6 text-primary-400" />
              </div>
              <p className="text-sm text-gray-500 mb-1">
                Escribe tu primera pregunta
              </p>
              <p className="text-xs text-gray-400 max-w-sm">
                Por ejemplo: "¿Cómo creo un RecyclerView en Android?" o
                "Explícame las funciones lambda en Kotlin"
              </p>
            </div>
          ) : (
            // Messages list
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
          <div className="border-t border-gray-200 bg-white px-4 py-3">
            <div className="max-w-3xl mx-auto">
              {remaining && remaining.remaining <= 0 && (
                <div className="flex items-center gap-2 text-sm text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-3">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>
                    Has alcanzado el límite de consultas por hora. Intenta de nuevo más tarde.
                  </span>
                </div>
              )}
              <div className="flex items-end gap-2">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Escribe tu pregunta..."
                  rows={1}
                  disabled={sendMessage.isPending || (remaining?.remaining ?? 1) <= 0}
                  className="flex-1 resize-none rounded-xl border border-gray-300 bg-gray-50 px-4 py-2.5 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <Button
                  onClick={handleSend}
                  disabled={
                    !input.trim() ||
                    sendMessage.isPending ||
                    (remaining?.remaining ?? 1) <= 0
                  }
                  size="icon"
                  className="shrink-0 h-10 w-10 rounded-xl"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
              <p className="text-xs text-gray-400 mt-2 text-center">
                Enter para enviar · Shift+Enter para nueva línea
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
