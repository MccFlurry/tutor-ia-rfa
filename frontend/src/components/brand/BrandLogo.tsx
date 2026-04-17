import { cn } from '@/lib/utils'

interface BrandLogoProps {
  variant?: 'compact' | 'full' | 'stacked'
  className?: string
  /**
   * When true, renders for use on dark backgrounds (inverted text).
   */
  onDark?: boolean
  /**
   * Optional label override — defaults to IESTP RFA copy.
   */
  subtitle?: string
}

/**
 * Institutional brand mark for IESTP República Federal de Alemania (Chiclayo).
 * Shield + "RFA" monogram, navy + heritage gold.
 */
export default function BrandLogo({
  variant = 'compact',
  className,
  onDark = false,
  subtitle,
}: BrandLogoProps) {
  const textColor = onDark ? 'text-white' : 'text-institutional-700'
  const subColor = onDark ? 'text-primary-200' : 'text-gray-500'

  return (
    <div className={cn('flex items-center gap-3', className)}>
      <Shield />
      {variant !== 'compact' && (
        <div className="flex flex-col leading-tight">
          <span className={cn('font-bold text-sm tracking-tight', textColor)}>
            Tutor IA — RFA
          </span>
          <span className={cn('text-[11px] font-medium', subColor)}>
            {subtitle ?? 'IESTP "República Federal de Alemania" · Chiclayo'}
          </span>
        </div>
      )}
      {variant === 'compact' && (
        <span className={cn('font-bold text-sm tracking-tight', textColor)}>
          Tutor IA
          <span className="ml-1 text-heritage-500">RFA</span>
        </span>
      )}
    </div>
  )
}

function Shield({ size = 32 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Escudo institucional IESTP RFA"
      className="shrink-0"
    >
      <defs>
        <linearGradient id="brand-navy" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor="#1e3a8a" />
          <stop offset="1" stopColor="#0b1845" />
        </linearGradient>
      </defs>
      <path
        d="M32 4 L58 12 V30 C58 45 46 56 32 60 C18 56 6 45 6 30 V12 Z"
        fill="url(#brand-navy)"
        stroke="#f59e0b"
        strokeWidth="2"
      />
      <rect x="14" y="40" width="36" height="3" rx="1.5" fill="#f59e0b" />
      <text
        x="32"
        y="34"
        fontFamily="Plus Jakarta Sans, system-ui, sans-serif"
        fontSize="18"
        fontWeight="800"
        fill="#ffffff"
        textAnchor="middle"
      >
        RFA
      </text>
    </svg>
  )
}
