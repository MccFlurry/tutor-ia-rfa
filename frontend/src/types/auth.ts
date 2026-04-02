export interface User {
  id: string
  email: string
  full_name: string
  role: 'student' | 'admin'
  is_active: boolean
  avatar_url?: string | null
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  full_name: string
  password: string
}

export interface AuthResponse {
  user: User
  access_token: string
  refresh_token: string
}

export interface TokenResponse {
  access_token: string
}

export interface MessageResponse {
  message: string
}
