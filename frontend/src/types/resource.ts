export type ResourceKind = 'video' | 'book' | 'article' | 'doc'

export interface LearningResource {
  id: number
  module_id: number | null
  topic_id: number | null
  kind: ResourceKind
  title: string
  url: string
  author?: string | null
  description?: string | null
  order_index: number
  is_active: boolean
}
