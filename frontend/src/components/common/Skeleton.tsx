import * as React from 'react'
import { cn } from '@/lib/utils'

type SkeletonVariant = 'text' | 'rect' | 'circle' | 'card'

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: SkeletonVariant
  width?: string
  height?: string
}

const variantClass: Record<SkeletonVariant, string> = {
  text: 'h-4 rounded',
  rect: 'rounded-lg',
  circle: 'rounded-full',
  card: 'rounded-2xl',
}

export default function Skeleton({
  variant = 'text',
  width,
  height,
  className,
  style,
  ...rest
}: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        'bg-muted motion-safe:animate-pulse',
        variantClass[variant],
        className
      )}
      style={{ width, height, ...style }}
      {...rest}
    />
  )
}

export function SkeletonLine({
  width = '100%',
  className,
}: {
  width?: string
  className?: string
}) {
  return <Skeleton variant="text" width={width} className={className} />
}

export function SkeletonCard({ className }: { className?: string }) {
  return <Skeleton variant="card" className={cn('h-32 w-full', className)} />
}
