import apiClient from './client'
import type { StudentLevel, Difficulty } from '@/types/assessment'

// ---------- Assessment Bank ----------
export interface AssessmentBankItem {
  id: number
  module_id: number
  question_text: string
  options: string[]
  correct_index: number
  difficulty: Difficulty
  is_active: boolean
  created_at: string
}

export interface AssessmentBankCreate {
  module_id: number
  question_text: string
  options: string[]
  correct_index: number
  difficulty: Difficulty
}

export interface AssessmentBankUpdate {
  question_text?: string
  options?: string[]
  correct_index?: number
  difficulty?: Difficulty
  is_active?: boolean
}

// ---------- User Levels ----------
export interface AdminUserLevelRow {
  user_id: string
  email: string
  full_name: string
  level: StudentLevel | null
  entry_score: number | null
  assessed_at: string | null
  last_reassessed_at: string | null
}

// ---------- Modules ----------
export interface ModuleAdmin {
  id: number
  title: string
  description: string | null
  order_index: number
  icon_name: string | null
  color_hex: string
  is_active: boolean
  created_at: string
}

export interface ModuleCreate {
  title: string
  description?: string | null
  order_index: number
  icon_name?: string | null
  color_hex?: string
  is_active?: boolean
}

export interface ModuleUpdate extends Partial<ModuleCreate> {}

// ---------- Topics ----------
export interface TopicAdmin {
  id: number
  module_id: number
  title: string
  content: string
  video_url: string | null
  order_index: number
  estimated_minutes: number
  has_quiz: boolean
  is_active: boolean
}

export interface TopicCreate {
  module_id: number
  title: string
  content?: string
  video_url?: string | null
  order_index: number
  estimated_minutes?: number
  has_quiz?: boolean
  is_active?: boolean
}

export interface TopicUpdate
  extends Partial<Omit<TopicCreate, 'module_id'>> {}

// ---------- Quiz Questions ----------
export interface QuizQuestionAdmin {
  id: number
  topic_id: number
  question_text: string
  options: string[]
  correct_option_index: number
  explanation: string | null
  order_index: number
}

export interface QuizQuestionCreate {
  topic_id: number
  question_text: string
  options: string[]
  correct_option_index: number
  explanation?: string | null
  order_index?: number
}

export interface QuizQuestionUpdate extends Partial<Omit<QuizQuestionCreate, 'topic_id'>> {}

// ---------- Coding Challenges ----------
export interface CodingChallengeAdmin {
  id: number
  topic_id: number
  title: string
  description: string
  initial_code: string | null
  language: string
  difficulty: Difficulty
  hints: string | null
  solution_code: string | null
  order_index: number
}

export interface CodingChallengeCreate {
  topic_id: number
  title: string
  description: string
  initial_code?: string | null
  language?: string
  difficulty?: Difficulty
  hints?: string | null
  solution_code?: string | null
  order_index?: number
}

export interface CodingChallengeUpdate extends Partial<Omit<CodingChallengeCreate, 'topic_id'>> {}

export interface GeneratedChallengePreview {
  title: string
  description: string
  hints: string
  solution_code: string
  difficulty: Difficulty
  language: string
}

// ---------- Documents ----------
export interface DocumentAdmin {
  id: string
  original_filename: string
  file_size_bytes: number | null
  mime_type: string | null
  status: 'pending' | 'processing' | 'active' | 'error'
  error_message: string | null
  chunk_count: number
  uploaded_by: string | null
  created_at: string
  processed_at: string | null
}

// ---------- Users ----------
export interface UserAdmin {
  id: string
  email: string
  full_name: string
  role: 'student' | 'admin'
  is_active: boolean
  created_at: string
  level: StudentLevel | null
}

export interface UserAdminUpdate {
  role?: 'student' | 'admin'
  is_active?: boolean
}

export const adminApi = {
  // Assessment bank
  listBank: (params?: { module_id?: number; difficulty?: Difficulty }) =>
    apiClient.get<AssessmentBankItem[]>('/admin/assessment-bank', { params }),
  createBankItem: (data: AssessmentBankCreate) =>
    apiClient.post<AssessmentBankItem>('/admin/assessment-bank', data),
  updateBankItem: (id: number, data: AssessmentBankUpdate) =>
    apiClient.put<AssessmentBankItem>(`/admin/assessment-bank/${id}`, data),
  deleteBankItem: (id: number) => apiClient.delete(`/admin/assessment-bank/${id}`),

  // User levels
  listUserLevels: () => apiClient.get<AdminUserLevelRow[]>('/admin/user-levels'),
  overrideUserLevel: (user_id: string, level: StudentLevel, reason: string) =>
    apiClient.put(`/admin/user-levels/${user_id}`, { level, reason }),

  // Modules
  listModules: () => apiClient.get<ModuleAdmin[]>('/admin/modules'),
  createModule: (data: ModuleCreate) => apiClient.post<ModuleAdmin>('/admin/modules', data),
  updateModule: (id: number, data: ModuleUpdate) =>
    apiClient.put<ModuleAdmin>(`/admin/modules/${id}`, data),
  deleteModule: (id: number) => apiClient.delete(`/admin/modules/${id}`),

  // Topics
  listTopics: (module_id?: number) =>
    apiClient.get<TopicAdmin[]>('/admin/topics', { params: { module_id } }),
  createTopic: (data: TopicCreate) => apiClient.post<TopicAdmin>('/admin/topics', data),
  updateTopic: (id: number, data: TopicUpdate) =>
    apiClient.put<TopicAdmin>(`/admin/topics/${id}`, data),
  deleteTopic: (id: number) => apiClient.delete(`/admin/topics/${id}`),

  // Quiz questions
  listQuizQuestions: (topic_id?: number) =>
    apiClient.get<QuizQuestionAdmin[]>('/admin/quiz-questions', { params: { topic_id } }),
  createQuizQuestion: (data: QuizQuestionCreate) =>
    apiClient.post<QuizQuestionAdmin>('/admin/quiz-questions', data),
  updateQuizQuestion: (id: number, data: QuizQuestionUpdate) =>
    apiClient.put<QuizQuestionAdmin>(`/admin/quiz-questions/${id}`, data),
  deleteQuizQuestion: (id: number) => apiClient.delete(`/admin/quiz-questions/${id}`),

  // Coding challenges
  listChallenges: (topic_id?: number) =>
    apiClient.get<CodingChallengeAdmin[]>('/admin/coding-challenges', { params: { topic_id } }),
  createChallenge: (data: CodingChallengeCreate) =>
    apiClient.post<CodingChallengeAdmin>('/admin/coding-challenges', data),
  updateChallenge: (id: number, data: CodingChallengeUpdate) =>
    apiClient.put<CodingChallengeAdmin>(`/admin/coding-challenges/${id}`, data),
  deleteChallenge: (id: number) => apiClient.delete(`/admin/coding-challenges/${id}`),
  generateChallenge: (topic_id: number, difficulty: Difficulty, target_level: StudentLevel) =>
    apiClient.post<GeneratedChallengePreview>('/admin/coding-challenges/generate', {
      topic_id,
      difficulty,
      target_level,
    }),

  // Documents
  listDocuments: () => apiClient.get<DocumentAdmin[]>('/admin/documents'),
  uploadDocument: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return apiClient.post<DocumentAdmin>('/admin/documents', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  reprocessDocument: (id: string) =>
    apiClient.post<DocumentAdmin>(`/admin/documents/${id}/reprocess`),
  deleteDocument: (id: string) => apiClient.delete(`/admin/documents/${id}`),

  // Users
  listUsers: () => apiClient.get<UserAdmin[]>('/admin/users'),
  updateUser: (id: string, data: UserAdminUpdate) =>
    apiClient.put<UserAdmin>(`/admin/users/${id}`, data),
}
