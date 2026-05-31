import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { chatApi } from '@/api/chat'
import toast from 'react-hot-toast'

/** Either a bare prompt (FloatingTutor) or a prompt with an abort signal (ChatPage cancel). */
export type SendMessageVariables = string | { content: string; signal?: AbortSignal }

/** True when an error is an aborted/cancelled request rather than a real failure. */
function isCanceledError(error: unknown): boolean {
  return (
    axios.isCancel(error) ||
    (error as { code?: string })?.code === 'ERR_CANCELED' ||
    (error as { name?: string })?.name === 'CanceledError'
  )
}

export function useChatSessions() {
  return useQuery({
    queryKey: ['chat-sessions'],
    queryFn: async () => {
      const { data } = await chatApi.listSessions()
      return data
    },
  })
}

export function useChatMessages(sessionId: string | null) {
  return useQuery({
    queryKey: ['chat-messages', sessionId],
    queryFn: async () => {
      if (!sessionId) return []
      const { data } = await chatApi.getMessages(sessionId)
      return data
    },
    enabled: !!sessionId,
  })
}

export function useCreateSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      const { data } = await chatApi.createSession()
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] })
    },
  })
}

export function useDeleteSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (sessionId: string) => {
      await chatApi.deleteSession(sessionId)
      return sessionId
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] })
    },
    onError: () => {
      toast.error('No se pudo eliminar la conversación. Intenta de nuevo.')
    },
  })
}

export function useSendMessage(sessionId: string | null) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (vars: SendMessageVariables) => {
      if (!sessionId) throw new Error('No session selected')
      const content = typeof vars === 'string' ? vars : vars.content
      const signal = typeof vars === 'string' ? undefined : vars.signal
      const { data } = await chatApi.sendMessage(sessionId, content, signal)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-messages', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] })
      queryClient.invalidateQueries({ queryKey: ['chat-remaining'] })
    },
    onError: (error: any) => {
      // User cancelled an in-flight response: not an error, stay quiet.
      if (isCanceledError(error)) return

      const status = error?.response?.status
      const detail = error?.response?.data?.detail

      if (status === 429) {
        toast.error(detail || 'Has alcanzado el límite de consultas por hora.')
      } else {
        toast.error('Error al enviar el mensaje. Intenta de nuevo.')
      }
    },
  })
}

export function useChatRemaining() {
  return useQuery({
    queryKey: ['chat-remaining'],
    queryFn: async () => {
      const { data } = await chatApi.getRemaining()
      return data
    },
    refetchInterval: 60000, // Refresh every minute
  })
}
