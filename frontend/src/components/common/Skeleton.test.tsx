import { describe, expect, it } from 'vitest'
import { render } from '@testing-library/react'
import Skeleton, { SkeletonCard, SkeletonLine } from './Skeleton'

describe('<Skeleton />', () => {
  it('applies aria-hidden so SR ignores it', () => {
    const { container } = render(<Skeleton />)
    expect(container.firstChild).toHaveAttribute('aria-hidden', 'true')
  })

  it.each(['text', 'rect', 'circle', 'card'] as const)(
    'accepts the %s variant',
    (variant) => {
      const { container } = render(<Skeleton variant={variant} />)
      expect(container.firstChild).toBeInTheDocument()
    }
  )

  it('applies width/height via inline style', () => {
    const { container } = render(<Skeleton width="200px" height="40px" />)
    const el = container.firstChild as HTMLElement
    expect(el.style.width).toBe('200px')
    expect(el.style.height).toBe('40px')
  })

  it('SkeletonLine delegates to text variant', () => {
    const { container } = render(<SkeletonLine width="50%" />)
    const el = container.firstChild as HTMLElement
    expect(el.style.width).toBe('50%')
  })

  it('SkeletonCard renders with card shape', () => {
    const { container } = render(<SkeletonCard />)
    expect(container.firstChild).toBeInTheDocument()
  })
})
