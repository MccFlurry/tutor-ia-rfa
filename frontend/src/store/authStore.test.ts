import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { useAuthStore } from './authStore'
import type { User } from '@/types/auth'

const USER: User = {
  id: 'u1',
  email: 'x@x.pe',
  full_name: 'Test',
  role: 'student',
  is_active: true,
  avatar_url: null,
  created_at: '2026-05-01T00:00:00Z',
}

describe('useAuthStore', () => {
  beforeEach(() => {
    window.localStorage.clear()
    // Reset zustand state between tests
    useAuthStore.setState({
      user: null,
      accessToken: null,
      isAuthenticated: false,
    })
  })

  afterEach(() => {
    window.localStorage.clear()
  })

  it('starts unauthenticated', () => {
    const s = useAuthStore.getState()
    expect(s.isAuthenticated).toBe(false)
    expect(s.user).toBeNull()
    expect(s.accessToken).toBeNull()
  })

  it('setAuth populates state and writes tokens', () => {
    useAuthStore.getState().setAuth(USER, 'access-tok', 'refresh-tok')
    const s = useAuthStore.getState()
    expect(s.isAuthenticated).toBe(true)
    expect(s.user).toEqual(USER)
    expect(s.accessToken).toBe('access-tok')
    expect(window.localStorage.getItem('access_token')).toBe('access-tok')
    expect(window.localStorage.getItem('refresh_token')).toBe('refresh-tok')
  })

  it('setUser updates only the user record', () => {
    useAuthStore.getState().setAuth(USER, 'a', 'r')
    useAuthStore.getState().setUser({ ...USER, full_name: 'Renamed' })
    expect(useAuthStore.getState().user?.full_name).toBe('Renamed')
    expect(useAuthStore.getState().accessToken).toBe('a')
  })

  it('logout clears state and storage', () => {
    useAuthStore.getState().setAuth(USER, 'a', 'r')
    useAuthStore.getState().logout()
    const s = useAuthStore.getState()
    expect(s.isAuthenticated).toBe(false)
    expect(s.user).toBeNull()
    expect(s.accessToken).toBeNull()
    expect(window.localStorage.getItem('access_token')).toBeNull()
    expect(window.localStorage.getItem('refresh_token')).toBeNull()
  })

  it('loadFromStorage restores token if present', () => {
    window.localStorage.setItem('access_token', 'persisted-tok')
    useAuthStore.getState().loadFromStorage()
    const s = useAuthStore.getState()
    expect(s.isAuthenticated).toBe(true)
    expect(s.accessToken).toBe('persisted-tok')
  })

  it('loadFromStorage is no-op without a stored token', () => {
    useAuthStore.getState().loadFromStorage()
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })
})
