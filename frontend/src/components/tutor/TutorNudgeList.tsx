import { useState } from 'react'
import TutorNudge from './TutorNudge'
import { useTutorNudges } from '@/hooks/useTutorNudges'
import type { NudgeContext } from '@/types/tutor'

interface Props {
  context: NudgeContext
  topicId?: number
  moduleId?: number
  score?: number
}

const DISMISS_KEY = 'tutor_dismissed_nudges'

function loadDismissed(): string[] {
  try {
    return JSON.parse(localStorage.getItem(DISMISS_KEY) || '[]')
  } catch {
    return []
  }
}

export default function TutorNudgeList({ context, topicId, moduleId, score }: Props) {
  const { data: nudges } = useTutorNudges({ context, topicId, moduleId, score })
  const [dismissed, setDismissed] = useState<string[]>(loadDismissed)

  // Result contexts are immediate, single-shot reinforcement — not dismissible/persisted.
  const isResult = context.endsWith('_result')

  const handleDismiss = (id: string) => {
    setDismissed((prev) => {
      if (prev.includes(id)) return prev
      const next = [...prev, id]
      try {
        localStorage.setItem(DISMISS_KEY, JSON.stringify(next))
      } catch {
        /* almacenamiento no disponible: se descarta solo en esta sesión */
      }
      return next
    })
  }

  if (!nudges || nudges.length === 0) return null
  const visible = isResult
    ? nudges
    : nudges.filter((n) => !dismissed.includes(String(n.id)))
  if (visible.length === 0) return null

  return (
    <div role="region" aria-label="Mensajes del tutor" className="space-y-3">
      {visible.map((n) => (
        <TutorNudge key={n.id} nudge={n} onDismiss={isResult ? undefined : handleDismiss} />
      ))}
    </div>
  )
}
