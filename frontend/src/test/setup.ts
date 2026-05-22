import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// Tear down React Testing Library between tests so DOM doesn't leak across them.
afterEach(() => {
  cleanup()
  window.localStorage.clear()
})

// jsdom doesn't implement matchMedia — themeStore + useMediaQuery need it.
if (!window.matchMedia) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    }),
  })
}
