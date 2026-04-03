import { Sparkles } from 'lucide-react'

export default function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 py-3">
      <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center shrink-0">
        <Sparkles className="w-4 h-4 text-primary-600" />
      </div>
      <div className="bg-gray-100 rounded-2xl rounded-tl-md px-4 py-3">
        <div className="flex items-center gap-1.5">
          <span className="text-sm text-gray-500">Tutor escribiendo</span>
          <div className="flex gap-1">
            <div
              className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: '0ms' }}
            />
            <div
              className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: '150ms' }}
            />
            <div
              className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: '300ms' }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
