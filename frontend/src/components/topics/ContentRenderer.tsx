import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CodeBlock from './CodeBlock'

interface ContentRendererProps {
  content: string
}

/**
 * Renders topic Markdown content. Heading levels are downshifted by one so
 * authored `# Title` becomes <h2> — the page already owns the single <h1>,
 * preserving a clean landmark hierarchy for screen readers.
 */
export default function ContentRenderer({ content }: ContentRendererProps) {
  return (
    <article className="prose prose-sm sm:prose-base prose-gray dark:prose-invert max-w-none prose-headings:text-foreground prose-p:leading-relaxed prose-p:text-foreground prose-li:text-foreground prose-strong:text-foreground prose-a:text-primary-600 dark:prose-a:text-primary-400 prose-code:text-primary-700 dark:prose-code:text-primary-300 prose-code:bg-primary-50 dark:prose-code:bg-primary/15 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:before:content-none prose-code:after:content-none prose-code:break-words prose-pre:overflow-x-auto prose-table:text-sm prose-th:bg-muted prose-th:px-3 prose-th:py-2 prose-td:px-3 prose-td:py-2 prose-blockquote:border-primary-500 prose-blockquote:bg-primary-50/50 dark:prose-blockquote:bg-primary/10 prose-blockquote:py-1 prose-blockquote:text-foreground">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children, ...props }) => <h2 {...props}>{children}</h2>,
          h2: ({ children, ...props }) => <h3 {...props}>{children}</h3>,
          h3: ({ children, ...props }) => <h4 {...props}>{children}</h4>,
          // Cap deepest rendered heading at h4 — h5/h6 are near-invisible in
          // most prose scales and carry weak semantic weight.
          h4: ({ children, ...props }) => <h4 {...props}>{children}</h4>,
          h5: ({ children, ...props }) => <h4 {...props}>{children}</h4>,
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
