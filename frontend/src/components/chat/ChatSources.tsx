import { useState } from 'react'
import { ChevronDown, FileText } from 'lucide-react'
import type { ChatSource } from '@/types/chat'

interface ChatSourcesProps {
  sources: ChatSource[]
}

export default function ChatSources({ sources }: ChatSourcesProps) {
  const [open, setOpen] = useState(false)

  if (!sources.length) return null

  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 transition-colors"
      >
        <FileText className="w-3 h-3" />
        <span>{sources.length} fuente{sources.length > 1 ? 's' : ''} del curso</span>
        <ChevronDown
          className={`w-3 h-3 transition-transform ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div className="mt-2 space-y-2">
          {sources.map((source, i) => (
            <div
              key={i}
              className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-xs"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-gray-700">
                  {source.document_name}
                </span>
                <span className="text-gray-400">
                  {Math.round(source.similarity * 100)}% relevancia
                </span>
              </div>
              <p className="text-gray-500 leading-relaxed">
                {source.content_preview}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
