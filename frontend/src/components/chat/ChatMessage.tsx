import { User, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CodeBlock from '@/components/topics/CodeBlock'
import ChatSources from './ChatSources'
import { formatTimeOfDay } from '@/lib/datetime'
import type { ChatMessage as ChatMessageType } from '@/types/chat'

interface ChatMessageProps {
  message: ChatMessageType
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const time = formatTimeOfDay(message.created_at)

  return (
    <div className={`flex items-start gap-3 py-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
          isUser ? 'bg-primary' : 'bg-primary/15'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-primary-foreground" />
        ) : (
          <Sparkles className="w-4 h-4 text-primary" />
        )}
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[85%] sm:max-w-[75%] ${
          isUser
            ? 'bg-primary text-primary-foreground rounded-2xl rounded-tr-md px-4 py-2.5'
            : 'bg-muted rounded-2xl rounded-tl-md px-4 py-3'
        }`}
      >
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-1.5 prose-p:leading-relaxed prose-p:text-foreground prose-li:text-foreground prose-strong:text-foreground prose-headings:text-foreground prose-code:text-primary-700 dark:prose-code:text-primary-300 prose-code:bg-background/60 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:before:content-none prose-code:after:content-none prose-pre:my-2 prose-ul:my-1.5 prose-ol:my-1.5 prose-li:my-0.5 prose-blockquote:border-primary-400 prose-blockquote:my-2">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '')
                  const codeString = String(children).replace(/\n$/, '')
                  if (match) {
                    return <CodeBlock language={match[1]}>{codeString}</CodeBlock>
                  }
                  return (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  )
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        {/* Sources for assistant messages */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <ChatSources sources={message.sources} />
        )}

        {time && (
          <time
            dateTime={message.created_at}
            className={`mt-1 block text-[11px] ${
              isUser ? 'text-right text-primary-foreground/70' : 'text-muted-foreground'
            }`}
          >
            {time}
          </time>
        )}
      </div>
    </div>
  )
}
