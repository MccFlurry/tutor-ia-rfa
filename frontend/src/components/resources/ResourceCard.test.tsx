import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import ResourceCard from './ResourceCard'
import type { LearningResource } from '@/types/resource'

function renderCard(over: Partial<LearningResource> = {}) {
  const r: LearningResource = {
    id: 1, module_id: 1, topic_id: null, kind: 'video',
    title: 'Kotlin Basics', url: 'https://youtu.be/abc',
    author: 'Google', description: null, order_index: 0, is_active: true, ...over,
  }
  return render(<ResourceCard resource={r} />)
}

describe('<ResourceCard />', () => {
  it('renders title and author', () => {
    renderCard()
    expect(screen.getByText('Kotlin Basics')).toBeInTheDocument()
    expect(screen.getByText(/Google/)).toBeInTheDocument()
  })

  it('links to the url, opening in a new tab safely', () => {
    renderCard()
    const link = screen.getByRole('link', { name: /Kotlin Basics/ })
    expect(link).toHaveAttribute('href', 'https://youtu.be/abc')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', expect.stringContaining('noopener'))
  })
})
