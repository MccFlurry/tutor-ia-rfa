import * as React from 'react'
import * as RadioGroupPrimitive from '@radix-ui/react-radio-group'
import { cn } from '@/lib/utils'

interface OptionRadioProps {
  value: string
  children: React.ReactNode
  className?: string
  disabled?: boolean
  id?: string
}

/**
 * Quiz/assessment option styled as a large clickable card.
 * MUST be rendered inside <RadioGroup>. Provides proper radiogroup semantics
 * (role=radio + aria-checked) for screen readers — replaces ad-hoc <button> options.
 */
const OptionRadio = React.forwardRef<HTMLButtonElement, OptionRadioProps>(
  ({ value, children, className, disabled, id }, ref) => {
    const generatedId = React.useId()
    const radioId = id ?? generatedId
    const labelId = `${radioId}-label`
    return (
      <RadioGroupPrimitive.Item
        ref={ref}
        value={value}
        id={radioId}
        disabled={disabled}
        aria-labelledby={labelId}
        className={cn(
          'group w-full text-left px-4 py-3 min-h-[44px] rounded-lg border-2 transition-colors text-sm leading-relaxed',
          'border-border bg-card text-card-foreground',
          'hover:border-border-strong',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
          'data-[state=checked]:border-primary data-[state=checked]:bg-primary-50',
          'data-[state=checked]:text-primary-800',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'dark:data-[state=checked]:bg-primary/10 dark:data-[state=checked]:text-primary-200',
          className
        )}
      >
        <span id={labelId} className="flex items-start gap-3">
          <span
            aria-hidden="true"
            className={cn(
              'mt-0.5 inline-flex items-center justify-center w-4 h-4 rounded-full border-2 shrink-0 transition-colors',
              'border-border-strong group-data-[state=checked]:border-primary'
            )}
          >
            <span className="w-2 h-2 rounded-full bg-primary opacity-0 group-data-[state=checked]:opacity-100 transition-opacity" />
          </span>
          <span className="flex-1">{children}</span>
        </span>
      </RadioGroupPrimitive.Item>
    )
  }
)
OptionRadio.displayName = 'OptionRadio'

export default OptionRadio
