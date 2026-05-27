import { useState } from 'react'
import { Database, FileCode, Users, ClipboardList, TrendingUp, BarChart3 } from 'lucide-react'
import { cn } from '@/lib/utils'
import CorpusTab from '@/components/admin/CorpusTab'
import ContentTab from '@/components/admin/ContentTab'
import UsersTab from '@/components/admin/UsersTab'
import BankTab from '@/components/admin/BankTab'
import LevelsTab from '@/components/admin/LevelsTab'
import StudentsReportTab from '@/components/admin/StudentsReportTab'

type TabId = 'reports' | 'corpus' | 'content' | 'users' | 'bank' | 'levels'

const TABS: { id: TabId; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'reports', label: 'Reportes', icon: BarChart3 },
  { id: 'corpus', label: 'Corpus RAG', icon: Database },
  { id: 'content', label: 'Contenido', icon: FileCode },
  { id: 'users', label: 'Usuarios', icon: Users },
  { id: 'bank', label: 'Banco Fallback', icon: ClipboardList },
  { id: 'levels', label: 'Niveles', icon: TrendingUp },
]

export default function AdminPage() {
  const [tab, setTab] = useState<TabId>('reports')

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 sm:px-6">
      <header className="mb-6">
        <span className="chip bg-heritage-100 text-heritage-700 dark:bg-heritage-700/20 dark:text-heritage-200 mb-2">Acceso admin</span>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-institutional-700 dark:text-institutional-100">
          Panel de Administración
        </h1>
        <p className="text-muted-foreground mt-1">
          IESTP "República Federal de Alemania" — Gestión del curso, corpus RAG, usuarios y personalización.
        </p>
        <span className="heritage-accent-bar mt-3" aria-hidden="true" />
      </header>

      {/* Tabs */}
      <div className="border-b border-border mb-6 overflow-x-auto">
        <div className="flex gap-1 min-w-max">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition',
                tab === t.id
                  ? 'border-primary-500 text-primary-700 dark:text-primary-300'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              )}
            >
              <t.icon className="w-4 h-4" />
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'reports' && <StudentsReportTab />}
      {tab === 'corpus' && <CorpusTab />}
      {tab === 'content' && <ContentTab />}
      {tab === 'users' && <UsersTab />}
      {tab === 'bank' && <BankTab />}
      {tab === 'levels' && <LevelsTab />}
    </div>
  )
}
