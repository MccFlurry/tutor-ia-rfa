import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'

/**
 * Moves keyboard/screen-reader focus to #main-content on every route change.
 * Skips the initial mount so SR users don't get an announcement before the page
 * loads. Pairs with AppLayout's <main id="main-content" tabIndex={-1}>.
 */
export function useFocusMain() {
  const location = useLocation()
  const isFirstRender = useRef(true)

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false
      return
    }
    const el = document.getElementById('main-content')
    if (el) {
      el.focus({ preventScroll: false })
    }
  }, [location.pathname])
}
