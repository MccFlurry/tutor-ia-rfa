import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import RecommendedResources from './RecommendedResources'

vi.mock('@/hooks/useRecommendedResources', () => ({
  useRecommendedResources: vi.fn(),
}))
import { useRecommendedResources } from '@/hooks/useRecommendedResources'

const mockHook = useRecommendedResources as unknown as ReturnType<typeof vi.fn>

const rec = (over = {}) => ({
  id: 1, module_id: 1, topic_id: null, kind: 'video', title: 'Video del emulador',
  url: 'http://x/1', author: null, description: null, order_index: 0, is_active: true,
  reason: 'Empieza por aquí', ...over,
})

describe('RecommendedResources', () => {
  it('renders the AI chip and reason when ai_ranked', () => {
    mockHook.mockReturnValue({
      data: { ai_ranked: true, level: 'beginner', recommendations: [rec()] },
    })
    render(<RecommendedResources moduleId={1} />)
    expect(screen.getByText(/Recomendado por IA/)).toBeInTheDocument()
    expect(screen.getByText('Empieza por aquí')).toBeInTheDocument()
  })

  it('hides chip and reasons in fallback', () => {
    mockHook.mockReturnValue({
      data: { ai_ranked: false, level: 'beginner', recommendations: [rec()] },
    })
    render(<RecommendedResources moduleId={1} />)
    expect(screen.queryByText(/Recomendado por IA/)).toBeNull()
    expect(screen.queryByText('Empieza por aquí')).toBeNull()
  })

  it('renders nothing when there are no recommendations', () => {
    mockHook.mockReturnValue({
      data: { ai_ranked: true, level: 'beginner', recommendations: [] },
    })
    const { container } = render(<RecommendedResources moduleId={1} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('shows the reason line only for items that have one', () => {
    mockHook.mockReturnValue({
      data: {
        ai_ranked: true,
        level: 'beginner',
        recommendations: [
          rec({ id: 1, reason: 'Empieza por aquí' }),
          rec({ id: 2, reason: null }),
        ],
      },
    })
    render(<RecommendedResources moduleId={1} />)
    // Dos recursos renderizados, pero solo el primero trae reason.
    expect(screen.getAllByText(/Empieza por aquí/)).toHaveLength(1)
  })
})
