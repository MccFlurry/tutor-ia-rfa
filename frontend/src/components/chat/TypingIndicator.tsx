import { Sparkles } from 'lucide-react'

export default function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 py-3">
      <div className="w-8 h-8 bg-primary/15 rounded-full flex items-center justify-center shrink-0">
        <Sparkles className="w-4 h-4 text-primary" />
      </div>
      <div className="bg-muted rounded-2xl rounded-tl-md px-4 py-3">
        <div className="flex items-center gap-1.5">
          <span className="text-sm text-muted-foreground">Tutor escribiendo</span>
          <div className="flex gap-1">
            <div
              className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-typing-dot motion-reduce:animate-none"
              style={{ animationDelay: '0ms' }}
            />
            <div
              className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-typing-dot motion-reduce:animate-none"
              style={{ animationDelay: '150ms' }}
            />
            <div
              className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-typing-dot motion-reduce:animate-none"
              style={{ animationDelay: '300ms' }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
