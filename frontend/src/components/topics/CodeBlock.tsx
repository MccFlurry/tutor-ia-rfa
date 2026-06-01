import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Copy, Check } from 'lucide-react'

interface CodeBlockProps {
  language: string
  children: string
}

export default function CodeBlock({ language, children }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(children)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative my-4 rounded-lg overflow-hidden">
      {/* Language label + copy button */}
      <div className="flex items-center justify-between bg-gray-800 px-4 py-1.5">
        <span className="text-xs text-gray-400 uppercase">{language}</span>
        {/* sr-only live region so screen readers announce the state change */}
        <span aria-live="polite" className="sr-only">
          {copied ? 'Código copiado' : ''}
        </span>
        <button
          type="button"
          onClick={handleCopy}
          aria-label={copied ? 'Código copiado' : 'Copiar código'}
          className="text-gray-400 hover:text-white transition text-xs flex items-center gap-1 min-h-[36px] px-2 py-1"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5" />
              Copiado
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              Copiar
            </>
          )}
        </button>
      </div>
      <SyntaxHighlighter
        language={language}
        style={vscDarkPlus}
        customStyle={{ margin: 0, borderRadius: 0, fontSize: '0.85rem', overflowX: 'auto' }}
      >
        {children}
      </SyntaxHighlighter>
    </div>
  )
}
