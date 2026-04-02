import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CodeBlock from './CodeBlock'

interface ContentRendererProps {
  content: string
}

export default function ContentRenderer({ content }: ContentRendererProps) {
  return (
    <article className="prose prose-gray max-w-none prose-headings:text-gray-900 prose-p:leading-relaxed prose-p:text-gray-700 prose-li:text-gray-700 prose-strong:text-gray-900 prose-a:text-primary-600 prose-code:text-primary-700 prose-code:bg-primary-50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:before:content-none prose-code:after:content-none prose-table:text-sm prose-th:bg-gray-100 prose-th:px-3 prose-th:py-2 prose-td:px-3 prose-td:py-2 prose-blockquote:border-primary-500 prose-blockquote:bg-primary-50/50 prose-blockquote:py-1 prose-blockquote:text-gray-700">
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
        {content}
      </ReactMarkdown>
    </article>
  )
}
