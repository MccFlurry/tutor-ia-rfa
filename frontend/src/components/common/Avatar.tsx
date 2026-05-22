import { useState } from 'react'
import { cn } from '@/lib/utils'

interface AvatarProps {
  fullName: string
  src?: string | null
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const SIZE_CLASS: Record<NonNullable<AvatarProps['size']>, string> = {
  sm: 'w-7 h-7 text-[10px]',
  md: 'w-9 h-9 text-xs',
  lg: 'w-12 h-12 text-base',
}

function initials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/)
  return ((parts[0]?.[0] ?? '') + (parts[1]?.[0] ?? '')).toUpperCase() || '??'
}

export default function Avatar({ fullName, src, size = 'md', className }: AvatarProps) {
  const [errored, setErrored] = useState(false)
  const showImage = src && !errored

  return (
    <div
      aria-hidden="true"
      className={cn(
        'inline-flex items-center justify-center rounded-full shrink-0 overflow-hidden',
        'bg-institutional-700 dark:bg-institutional-500 text-white font-bold shadow-brand-sm',
        SIZE_CLASS[size],
        className
      )}
    >
      {showImage ? (
        <img
          src={src!}
          alt=""
          className="w-full h-full object-cover"
          onError={() => setErrored(true)}
          loading="lazy"
        />
      ) : (
        <span>{initials(fullName)}</span>
      )}
    </div>
  )
}
