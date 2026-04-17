import { useState } from 'react'
import { Database, FileCode, Users, ClipboardList, TrendingUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import CorpusTab from '@/components/admin/CorpusTab'
import ContentTab from '@/components/admin/ContentTab'
import UsersTab from '@/components/admin/UsersTab'
import BankTab from '@/components/admin/BankTab'
import LevelsTab from '@/components/admin/LevelsTab'

type TabId = 'corpus' | 'content' | 'users' | 'bank' | 'levels'

const TABS: { id: TabId; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'corpus', label: 'Corpus RAG', icon: Database },
  { id: 'content', label: 'Contenido', icon: FileCode },
  { id: 'users', label: 'Usuarios', icon: Users },
  { id: 'bank', label: 'Banco Fallback', icon: ClipboardList },
  { id: 'levels', label: 'Niveles', icon: TrendingUp },
]

export default function AdminPage() {
  const [tab, setTab] = useState<TabId>('corpus')

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 sm:px-6">
      <header className="mb-6">
        <span className="chip bg-heritage-100 text-heritage-700 mb-2">Acceso admin</span>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-institutional-700">
          Panel de Administración
        </h1>
        <p className="text-gray-600 mt-1">
          IESTP "República Federal de Alemania" — Gestión del curso, corpus RAG, usuarios y personalización.
        </p>
        <span className="heritage-accent-bar mt-3" aria-hidden="true" />
      </header>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6 overflow-x-auto">
        <div className="flex gap-1 min-w-max">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition',
                tab === t.id
                  ? 'border-primary-500 text-primary-700'
                  : 'border-transparent text-gray-500 hover:text-gray-800'
              )}
            >
              <t.icon className="w-4 h-4" />
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'corpus' && <CorpusTab />}
      {tab === 'content' && <ContentTab />}
      {tab === 'users' && <UsersTab />}
      {tab === 'bank' && <BankTab />}
      {tab === 'levels' && <LevelsTab />}
    </div>
  )
}
