// Locale-aware date helpers (Spanish, Peru). Used in chat surfaces.

const relativeFormatter = new Intl.RelativeTimeFormat('es', { numeric: 'auto' })

const MINUTE = 60_000
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR
const WEEK = 7 * DAY

/**
 * Short relative time for session/message recency: "hace 5 min", "ayer", or a
 * `12 may` date once it is older than a week. Returns '' for missing/invalid input.
 */
export function formatRelativeTime(iso?: string | null): string {
  if (!iso) return ''
  const t = new Date(iso).getTime()
  if (Number.isNaN(t)) return ''

  const diff = t - Date.now()
  const abs = Math.abs(diff)

  if (abs < MINUTE) return 'ahora'
  if (abs < HOUR) return relativeFormatter.format(Math.round(diff / MINUTE), 'minute')
  if (abs < DAY) return relativeFormatter.format(Math.round(diff / HOUR), 'hour')
  if (abs < WEEK) return relativeFormatter.format(Math.round(diff / DAY), 'day')

  return new Intl.DateTimeFormat('es-PE', { day: '2-digit', month: 'short' }).format(t)
}

/** Time-of-day stamp for chat bubbles, e.g. "14:32". '' for missing/invalid input. */
export function formatTimeOfDay(iso?: string | null): string {
  if (!iso) return ''
  const t = new Date(iso).getTime()
  if (Number.isNaN(t)) return ''
  return new Intl.DateTimeFormat('es-PE', { hour: '2-digit', minute: '2-digit' }).format(t)
}
