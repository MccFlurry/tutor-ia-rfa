import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import BrandLogo from './BrandLogo'

describe('<BrandLogo />', () => {
  it('renders official logo image', () => {
    render(<BrandLogo />)
    const img = screen.getByRole('img') as HTMLImageElement
    expect(img.src).toContain('/logo-iestp-rfa.png')
    expect(img.alt).toContain('IESTP')
  })

  it('compact variant shows short label', () => {
    render(<BrandLogo variant="compact" />)
    expect(screen.getByText('Tutor IA')).toBeInTheDocument()
    expect(screen.getByText('RFA')).toBeInTheDocument()
  })

  it('full variant shows expanded subtitle', () => {
    render(<BrandLogo variant="full" />)
    expect(
      screen.getByText(/IESTP "República Federal de Alemania"/)
    ).toBeInTheDocument()
  })

  it('honors custom size', () => {
    render(<BrandLogo size={96} />)
    const img = screen.getByRole('img') as HTMLImageElement
    expect(img.width).toBe(96)
    expect(img.height).toBe(96)
  })

  it('accepts a custom subtitle override', () => {
    render(<BrandLogo variant="stacked" subtitle="Subtitle X" />)
    expect(screen.getByText('Subtitle X')).toBeInTheDocument()
  })
})
