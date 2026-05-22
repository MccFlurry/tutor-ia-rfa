import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from './button'

describe('<Button />', () => {
  it('renders a real <button> by default', () => {
    render(<Button>Click</Button>)
    expect(screen.getByRole('button', { name: 'Click' })).toBeInTheDocument()
  })

  it('fires onClick', async () => {
    const onClick = vi.fn()
    const user = userEvent.setup()
    render(<Button onClick={onClick}>Press</Button>)
    await user.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalledOnce()
  })

  it('respects disabled', async () => {
    const onClick = vi.fn()
    const user = userEvent.setup()
    render(
      <Button disabled onClick={onClick}>
        Off
      </Button>
    )
    await user.click(screen.getByRole('button'))
    expect(onClick).not.toHaveBeenCalled()
  })

  it.each(['destructive', 'outline', 'secondary', 'ghost', 'link'] as const)(
    'accepts variant %s without crashing',
    (variant) => {
      render(<Button variant={variant}>x</Button>)
      expect(screen.getByRole('button')).toBeInTheDocument()
    }
  )

  it('asChild=true renders the child element rather than a <button>', () => {
    render(
      <Button asChild>
        <a href="/x">Link</a>
      </Button>
    )
    const link = screen.getByRole('link', { name: 'Link' })
    expect(link).toBeInTheDocument()
    expect(link.tagName).toBe('A')
  })
})
