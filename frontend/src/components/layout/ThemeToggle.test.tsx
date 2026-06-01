import { beforeEach, describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ThemeToggle from './ThemeToggle'
import { useThemeStore } from '@/store/themeStore'

const STORAGE_KEY = 'tutor-rfa.theme'

describe('<ThemeToggle />', () => {
  beforeEach(() => {
    document.documentElement.classList.remove('dark')
    window.localStorage.clear()
    window.localStorage.setItem(STORAGE_KEY, 'light')
    useThemeStore.setState({ pref: 'light', isDark: false })
  })

  it('renders an accessible toggle button', () => {
    render(<ThemeToggle />)
    expect(
      screen.getByRole('button', { name: /actual: claro/i })
    ).toBeInTheDocument()
  })

  it('cycles light → dark on click', async () => {
    const user = userEvent.setup()
    render(<ThemeToggle />)
    await user.click(screen.getByRole('button'))
    expect(useThemeStore.getState().pref).toBe('dark')
  })

  it('cycles dark → system → light', async () => {
    useThemeStore.setState({ pref: 'dark', isDark: true })
    const user = userEvent.setup()
    render(<ThemeToggle />)
    await user.click(screen.getByRole('button'))
    expect(useThemeStore.getState().pref).toBe('system')

    await user.click(screen.getByRole('button'))
    expect(useThemeStore.getState().pref).toBe('light')
  })
})
