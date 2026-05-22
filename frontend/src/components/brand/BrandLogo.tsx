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
  /**
   * Render size of the institutional shield in px (square).
   */
  size?: number
}

/**
 * Institutional brand mark for IESTP "República Federal de Alemania" (Chiclayo).
 * Uses the official heraldic shield (gear, satellite, books, nurse, vehicle)
 * served from /logo-iestp-rfa.png.
 */
export default function BrandLogo({
  variant = 'compact',
  className,
  onDark = false,
  subtitle,
  size = 40,
}: BrandLogoProps) {
  const textColor = onDark ? 'text-white' : 'text-institutional-700'
  const subColor = onDark ? 'text-primary-200' : 'text-muted-foreground'

  return (
    <div className={cn('flex items-center gap-3', className)}>
      <img
        src="/logo-iestp-rfa.png"
        alt='Escudo oficial IESTP "República Federal de Alemania" — Chiclayo'
        width={size}
        height={size}
        loading="eager"
        decoding="async"
        className={cn(
          'shrink-0 object-contain drop-shadow-sm',
          onDark && 'drop-shadow-[0_1px_4px_rgba(0,0,0,0.35)]'
        )}
        style={{ width: size, height: size }}
      />
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
