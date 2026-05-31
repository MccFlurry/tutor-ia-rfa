# Asistente Flotante del Tutor (Fase 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un asistente flotante del tutor IA presente en toda pantalla con layout, que abre un chat RAG contextual reusando el pipeline de chat existente.

**Architecture:** Componente `FloatingTutor` montado una vez en `AppLayout`. Burbuja fija (bottom-right) → abre un panel con un mini-chat. Reusa los hooks existentes (`useCreateSession`, `useChatMessages`, `useSendMessage`, `useChatRemaining`) y los componentes `ChatMessage`/`TypingIndicator`. CERO cambios de backend — usa el endpoint `/chat` y su rate limit (20/h) ya implementados.

**Tech Stack:** React 18 + TypeScript + Tailwind + TanStack Query + lucide-react + react-router-dom v6 + Vitest/RTL.

**Scope (spec §5):** burbuja flotante; al abrir crea/usa una sesión de chat; envía vía RAG existente; muestra "X/Y consultas"; respeta rate limit (manejo 429 ya en `useSendMessage`); móvil a pantalla completa; a11y (ESC cierra, botón 44px, `role="dialog"`, foco). Precarga ligera de contexto: si la ruta es un tema, prefija el input. NO se monta en Login (vive dentro de `AppLayout`).

**Convención:** rama `feat/tutor-floating` desde `main`. Comandos frontend desde `C:\tutor-ia-rfa\frontend`.

---

### Task 0: Crear rama

- [ ] **Step 1:**
```bash
git checkout main
git checkout -b feat/tutor-floating
```

---

### Task 1: Componente `FloatingTutor` + test

**Files:**
- Create: `frontend/src/components/tutor/FloatingTutor.tsx`
- Test: `frontend/src/components/tutor/FloatingTutor.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

```tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import FloatingTutor from './FloatingTutor'

// Mock de los hooks de chat: el smoke test no debe tocar la red.
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
```

- [ ] **Step 2: Correr para verificar que falla**

Run (desde `C:\tutor-ia-rfa\frontend`): `npx vitest run src/components/tutor/FloatingTutor.test.tsx`
Expected: FAIL (módulo no existe).

- [ ] **Step 3: Implementar el componente**

```tsx
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
import type { ChatMessage } from '@/types/chat'

export default function FloatingTutor() {
  const [open, setOpen] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [input, setInput] = useState('')
  const [optimistic, setOptimistic] = useState<ChatMessage[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const location = useLocation()

  const createSession = useCreateSession()
  const { data: serverMessages = [] } = useChatMessages(sessionId)
  const { data: remaining } = useChatRemaining()
  const sendMessage = useSendMessage(sessionId)

  const messages = [...serverMessages, ...optimistic]

  const handleOpen = useCallback(async () => {
    setOpen(true)
    // Precarga ligera de contexto: si estamos en un tema, prefija el input.
    if (!input && location.pathname.startsWith('/topics/')) {
      setInput('Sobre el tema actual, ')
    }
    if (!sessionId) {
      try {
        const s = await createSession.mutateAsync()
        setSessionId(s.id)
      } catch {
        // si falla la creación, el panel sigue abierto; el usuario puede reintentar
      }
    }
  }, [sessionId, createSession, input, location.pathname])

  // ESC cierra el panel
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open])

  // auto-scroll al final
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, sendMessage.isPending])

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
    } finally {
      setOptimistic([])
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
          {/* Header */}
          <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
            <Sparkles className="h-5 w-5 text-primary" aria-hidden="true" />
            <span className="font-semibold text-foreground">Tutor IA</span>
            {remaining && (
              <span
                className="ml-auto text-xs text-muted-foreground tabular-nums"
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

          {/* Mensajes */}
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

          {/* Input */}
          <div className="border-t border-border p-2">
            {rateLimited && (
              <p role="alert" className="text-xs text-warning px-1 pb-2">
                Has alcanzado el límite de consultas por hora. Intenta más tarde.
              </p>
            )}
            <div className="flex items-end gap-2">
              <Textarea
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
```

- [ ] **Step 4: Correr para verificar que pasa**

Run: `npx vitest run src/components/tutor/FloatingTutor.test.tsx`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/tutor/FloatingTutor.tsx frontend/src/components/tutor/FloatingTutor.test.tsx
git commit -m "feat(tutor): asistente flotante FloatingTutor con test"
```

> Nota de verificación: antes de implementar, confirmar en `frontend/src/types/chat.ts` que `ChatMessage` tiene exactamente los campos usados en el objeto optimista (`id, role, content, sources, created_at`). Es el mismo objeto usado en `ChatPage.tsx`, así que debería coincidir; si difiere, ajustar el objeto `temp`.

---

### Task 2: Montar en `AppLayout`

**Files:**
- Modify: `frontend/src/components/layout/AppLayout.tsx`

- [ ] **Step 1: Importar y montar**

En `frontend/src/components/layout/AppLayout.tsx`, importar `FloatingTutor` y renderizarlo junto a `<ReassessmentModal />` (último hijo del contenedor raíz), de modo que aparezca en todas las rutas con layout:

```tsx
import FloatingTutor from '@/components/tutor/FloatingTutor'
// ...
      <ReassessmentModal />
      <FloatingTutor />
    </div>
```

(El layout solo envuelve rutas autenticadas con nivel; Login y `/assessment` quedan fuera, como se desea.)

- [ ] **Step 2: Verificar build + suite completa**

Run (desde `C:\tutor-ia-rfa\frontend`): `npx tsc --noEmit && npx vitest run`
Expected: tsc sin errores; toda la suite pasa.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/layout/AppLayout.tsx
git commit -m "feat(tutor): montar asistente flotante en AppLayout"
```

---

### Task 3: Documentación

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/matriz-trazabilidad-ISO25010.md`

- [ ] **Step 1: Registrar en CLAUDE.md**

Añadir al bullet de la fase de acompañamiento (creada en Fase 1, en "Fases completadas") una línea o sub-bullet indicando: "Fase 2 ✅ — asistente flotante (`components/tutor/FloatingTutor.tsx`) montado en `AppLayout`, reusa el chat RAG existente (`/chat`) con sesión contextual, contador de consultas y rate limit 20/h; sin cambios de backend."

- [ ] **Step 2: Matriz ISO**

En `docs/matriz-trazabilidad-ISO25010.md`, en la tabla de extensión post-Sprint 7 (donde está `RF-NEW-TUTOR-01`), agregar `RF-NEW-TUTOR-02`: "Asistente flotante del tutor (chat RAG omnipresente)" ↔ Servicio `/chat` reusado + `components/tutor/FloatingTutor.tsx` ↔ Tests `frontend FloatingTutor.test.tsx` + (cobertura backend `/chat` existente) ↔ Subcaracterística "Operabilidad / Pertinencia funcional" ↔ implementado. Mantener el MISMO número de columnas que las filas vecinas; NO renumerar `RF-01..RF-33`.

- [ ] **Step 3: Guardian ISO (si aplica)**

Run (desde `C:\tutor-ia-rfa\backend`): `pytest tests/integration/test_iso25010.py -v`. Si falla por la fila nueva (p.ej. exige que el archivo de test exista), ajustar la referencia a archivos que existan. Si pasa, continuar.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md docs/matriz-trazabilidad-ISO25010.md
git commit -m "docs(tutor): registrar Fase 2 asistente flotante y RF en matriz ISO"
```

---

## Verificación final de Fase 2

- [ ] `npx tsc --noEmit` sin errores y `npx vitest run` verde.
- [ ] La burbuja aparece en pantallas con layout (Dashboard/Topic/etc.) y NO en Login/Assessment.
- [ ] Abrir → crea sesión → enviar pregunta → respuesta RAG; contador y rate limit visibles; ESC y botón cierran.
- [ ] Móvil: panel a pantalla completa.
- [ ] CLAUDE.md y matriz ISO actualizados.

Al cerrar Fase 2, decidir con el usuario si seguir con Fase 3 (banco de recursos curados — videos/libros).
