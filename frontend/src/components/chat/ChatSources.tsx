import { useState, useId } from 'react'
import { ChevronDown, FileText } from 'lucide-react'
import type { ChatSource } from '@/types/chat'

interface ChatSourcesProps {
  sources: ChatSource[]
}

export default function ChatSources({ sources }: ChatSourcesProps) {
  const [open, setOpen] = useState(false)
  const id = useId()
  const listId = `chat-sources-${id}`

  if (!sources.length) return null

  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-controls={listId}
        className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        <FileText className="w-3 h-3" />
        <span>{sources.length} fuente{sources.length > 1 ? 's' : ''} del curso</span>
        <ChevronDown
          className={`w-3 h-3 transition-transform ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div
          id={listId}
          className="mt-2 space-y-2 opacity-0 animate-in fade-in slide-in-from-top-1 duration-150 fill-mode-forwards"
          style={{ animationFillMode: 'forwards' }}
        >
          {sources.map((source, i) => (
            <div
              key={i}
              className="bg-muted border border-border rounded-lg px-3 py-2 text-xs"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-foreground">
                  {source.document_name}
                </span>
                <span className="text-muted-foreground">
                  {Math.round(source.similarity * 100)}% relevancia
                </span>
              </div>
              <p className="text-muted-foreground leading-relaxed">
                {source.content_preview}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
