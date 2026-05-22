import { describe, expect, it } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Avatar from './Avatar'

describe('<Avatar />', () => {
  it('renders initials from full name', () => {
    render(<Avatar fullName="Roger Zavaleta" />)
    expect(screen.getByText('RZ')).toBeInTheDocument()
  })

  it('falls back to ?? when name is whitespace', () => {
    render(<Avatar fullName="   " />)
    expect(screen.getByText('??')).toBeInTheDocument()
  })

  it('takes first two name parts only (uppercase)', () => {
    render(<Avatar fullName="ana del campo" />)
    expect(screen.getByText('AD')).toBeInTheDocument()
  })

  it('shows the image when src provided and not errored', () => {
    const { container } = render(<Avatar fullName="Test" src="/avatar.png" />)
    const img = container.querySelector('img') as HTMLImageElement
    expect(img).not.toBeNull()
    expect(img.src).toContain('/avatar.png')
  })

  it('falls back to initials after image load error', () => {
    const { container } = render(<Avatar fullName="Roger Zavaleta" src="/missing.png" />)
    const img = container.querySelector('img')!
    fireEvent.error(img)
    expect(screen.getByText('RZ')).toBeInTheDocument()
  })
})
