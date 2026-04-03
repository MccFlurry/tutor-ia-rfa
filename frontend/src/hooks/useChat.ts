import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chatApi } from '@/api/chat'
import toast from 'react-hot-toast'

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
  })
}

export function useSendMessage(sessionId: string | null) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (content: string) => {
      if (!sessionId) throw new Error('No session selected')
      const { data } = await chatApi.sendMessage(sessionId, content)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat-messages', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] })
      queryClient.invalidateQueries({ queryKey: ['chat-remaining'] })
    },
    onError: (error: any) => {
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
