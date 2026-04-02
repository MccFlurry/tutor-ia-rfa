import { useNavigate } from 'react-router-dom'
import { Lock } from 'lucide-react'
import * as LucideIcons from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import type { Module } from '@/types/module'

interface ModuleCardProps {
  module: Module
}

function getIcon(iconName: string | null) {
  if (!iconName) return LucideIcons.BookOpen
  const pascal = iconName
    .split('-')
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join('')
  return (LucideIcons as Record<string, any>)[pascal] || LucideIcons.BookOpen
}

function getStatusBadge(module: Module) {
  if (module.is_locked) return { label: 'Bloqueado', variant: 'secondary' as const }
  if (module.progress_pct >= 100) return { label: 'Completado', variant: 'default' as const }
  if (module.progress_pct > 0) return { label: 'En progreso', variant: 'outline' as const }
  return { label: 'No iniciado', variant: 'secondary' as const }
}

export default function ModuleCard({ module }: ModuleCardProps) {
  const navigate = useNavigate()
  const Icon = getIcon(module.icon_name)
  const status = getStatusBadge(module)

  const handleClick = () => {
    if (!module.is_locked) {
      navigate(`/modules/${module.id}`)
    }
  }

  return (
    <div
      onClick={handleClick}
      className={`bg-white rounded-xl border border-gray-200 p-6 transition-all ${
        module.is_locked
          ? 'opacity-60 cursor-not-allowed grayscale'
          : 'cursor-pointer hover:shadow-md hover:border-gray-300'
      }`}
    >
      {/* Icon + Badge row */}
      <div className="flex items-start justify-between mb-4">
        <div
          className="w-12 h-12 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: module.is_locked ? '#e5e7eb' : module.color_hex + '20' }}
        >
          {module.is_locked ? (
            <Lock className="w-6 h-6 text-gray-400" />
          ) : (
            <Icon className="w-6 h-6" style={{ color: module.color_hex }} />
          )}
        </div>
        <Badge variant={status.variant}>{status.label}</Badge>
      </div>

      {/* Title + Description */}
      <h3 className="font-semibold text-gray-900 mb-1 line-clamp-2">
        {module.title}
      </h3>
      <p className="text-sm text-gray-500 mb-4 line-clamp-2">
        {module.description}
      </p>

      {/* Progress */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-gray-500">
          <span>{module.completed_topics} de {module.total_topics} temas</span>
          <span>{Math.round(module.progress_pct)}%</span>
        </div>
        <Progress value={module.progress_pct} className="h-2" />
      </div>
    </div>
  )
}
