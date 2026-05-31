import TutorNudge from './TutorNudge'
import { useTutorNudges } from '@/hooks/useTutorNudges'
import type { NudgeContext } from '@/types/tutor'

interface Props {
  context: NudgeContext
  topicId?: number
  moduleId?: number
  score?: number
}

export default function TutorNudgeList({ context, topicId, moduleId, score }: Props) {
  const { data: nudges } = useTutorNudges({ context, topicId, moduleId, score })
  if (!nudges || nudges.length === 0) return null
  return (
    <div role="region" aria-label="Mensajes del tutor" className="space-y-3">
      {nudges.map((n) => (
        <TutorNudge key={n.id} nudge={n} />
      ))}
    </div>
  )
}
