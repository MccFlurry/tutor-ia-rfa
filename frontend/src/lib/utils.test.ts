import { describe, expect, it } from 'vitest'
import { cn } from './utils'

describe('cn (className merger)', () => {
  it('joins multiple strings', () => {
    expect(cn('a', 'b', 'c')).toBe('a b c')
  })

  it('removes falsy values', () => {
    expect(cn('a', false, null, undefined, 0 as unknown as string, 'b')).toBe('a b')
  })

  it('merges conflicting tailwind classes — last one wins', () => {
    // tailwind-merge: px-2 + px-4 → px-4
    expect(cn('px-2 py-1', 'px-4')).toBe('py-1 px-4')
  })

  it('accepts arrays + objects per clsx contract', () => {
    expect(cn(['a', 'b'], { c: true, d: false })).toBe('a b c')
  })
})
