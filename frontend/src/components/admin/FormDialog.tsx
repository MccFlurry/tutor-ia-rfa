import { useEffect, useRef, useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'

export interface FormField {
  name: string
  label: string
  type: 'text' | 'textarea' | 'number' | 'select'
  options?: { value: string; label: string }[]
  defaultValue?: string
  required?: boolean
  placeholder?: string
  helpText?: string
}

export interface FormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  fields: FormField[]
  submitLabel?: string
  pending?: boolean
  onSubmit: (values: Record<string, string>) => void
}

export default function FormDialog({
  open,
  onOpenChange,
  title,
  fields,
  submitLabel = 'Guardar',
  pending = false,
  onSubmit,
}: FormDialogProps) {
  const firstRef = useRef<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement | null>(null)
  const [errors, setErrors] = useState<Record<string, boolean>>({})

  // Reset errors when dialog opens/closes
  useEffect(() => {
    if (!open) setErrors({})
  }, [open])

  // Focus first field on open
  useEffect(() => {
    if (open) {
      const timer = setTimeout(() => {
        firstRef.current?.focus()
      }, 50)
      return () => clearTimeout(timer)
    }
  }, [open])

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const form = e.currentTarget
    const data = new FormData(form)
    const values: Record<string, string> = {}
    const newErrors: Record<string, boolean> = {}
    let hasError = false

    for (const field of fields) {
      const val = (data.get(field.name) as string | null) ?? ''
      values[field.name] = val
      if (field.required && !val.trim()) {
        newErrors[field.name] = true
        hasError = true
      }
    }

    setErrors(newErrors)
    if (hasError) return
    onSubmit(values)
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!pending) onOpenChange(o) }}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} noValidate className="space-y-4 py-2">
          {fields.map((field, idx) => {
            const fieldId = `form-field-${field.name}`
            const hasError = errors[field.name]
            const isFirst = idx === 0

            return (
              <div key={field.name} className="space-y-1.5">
                <Label htmlFor={fieldId}>
                  {field.label}
                  {field.required && (
                    <span className="text-destructive ml-1" aria-hidden="true">*</span>
                  )}
                </Label>

                {field.type === 'textarea' && (
                  <Textarea
                    id={fieldId}
                    name={field.name}
                    defaultValue={field.defaultValue ?? ''}
                    placeholder={field.placeholder}
                    required={field.required}
                    aria-describedby={field.helpText ? `${fieldId}-help` : undefined}
                    aria-invalid={hasError || undefined}
                    ref={isFirst ? (el) => { firstRef.current = el } : undefined}
                    className={cn(hasError && 'border-destructive focus-visible:ring-destructive')}
                  />
                )}

                {(field.type === 'text' || field.type === 'number') && (
                  <Input
                    id={fieldId}
                    name={field.name}
                    type={field.type}
                    defaultValue={field.defaultValue ?? ''}
                    placeholder={field.placeholder}
                    required={field.required}
                    aria-describedby={field.helpText ? `${fieldId}-help` : undefined}
                    aria-invalid={hasError || undefined}
                    ref={isFirst ? (el) => { firstRef.current = el } : undefined}
                    className={cn(hasError && 'border-destructive focus-visible:ring-destructive')}
                  />
                )}

                {field.type === 'select' && (
                  <select
                    id={fieldId}
                    name={field.name}
                    defaultValue={field.defaultValue ?? (field.options?.[0]?.value ?? '')}
                    required={field.required}
                    aria-describedby={field.helpText ? `${fieldId}-help` : undefined}
                    aria-invalid={hasError || undefined}
                    ref={isFirst ? (el) => { firstRef.current = el } : undefined}
                    className={cn(
                      'flex h-11 w-full rounded-lg border border-input bg-background px-4 py-2 text-base text-foreground',
                      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                      'focus-visible:border-primary',
                      hasError && 'border-destructive focus-visible:ring-destructive'
                    )}
                  >
                    {field.options?.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                )}

                {field.helpText && (
                  <p id={`${fieldId}-help`} className="text-xs text-muted-foreground">
                    {field.helpText}
                  </p>
                )}

                {hasError && (
                  <p className="text-xs text-destructive" role="alert">
                    Campo obligatorio
                  </p>
                )}
              </div>
            )
          })}

          <DialogFooter className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={pending}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={pending}>
              {pending ? 'Guardando...' : submitLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
