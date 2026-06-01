import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Sun, Moon, Monitor, User as UserIcon, Lock, Palette, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import PageHeader from '@/components/common/PageHeader'
import Avatar from '@/components/common/Avatar'
import { cn } from '@/lib/utils'
import { usersApi } from '@/api/users'
import { useAuthStore } from '@/store/authStore'
import { useThemeStore, type ThemePref } from '@/store/themeStore'

function ProfileTab() {
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)
  const queryClient = useQueryClient()

  const [fullName, setFullName] = useState(user?.full_name ?? '')
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url ?? '')

  const updateMutation = useMutation({
    mutationFn: () =>
      usersApi.updateMe({ full_name: fullName, avatar_url: avatarUrl || undefined }).then((r) => r.data),
    onSuccess: (data) => {
      setUser(data)
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Perfil actualizado')
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || 'Error al actualizar perfil')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!fullName.trim()) {
      toast.error('El nombre no puede estar vacío')
      return
    }
    updateMutation.mutate()
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5 max-w-md">
      <div className="flex items-center gap-4">
        <Avatar fullName={fullName || user?.full_name || 'U'} src={avatarUrl} size="lg" />
        <div className="text-sm text-muted-foreground">
          <p className="font-medium text-foreground">{user?.email}</p>
          <p className="capitalize">{user?.role === 'admin' ? 'Administrador' : 'Estudiante'}</p>
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="profile-name">Nombre completo</Label>
        <Input
          id="profile-name"
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
          autoComplete="name"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="profile-avatar">URL de avatar (opcional)</Label>
        <Input
          id="profile-avatar"
          type="url"
          value={avatarUrl}
          onChange={(e) => setAvatarUrl(e.target.value)}
          placeholder="https://..."
          autoComplete="off"
          aria-describedby="profile-avatar-help"
        />
        <p id="profile-avatar-help" className="text-xs text-muted-foreground">
          Pega un enlace a una imagen pública. Déjalo vacío para usar tus iniciales.
        </p>
      </div>

      <Button type="submit" disabled={updateMutation.isPending}>
        {updateMutation.isPending ? 'Guardando...' : 'Guardar cambios'}
      </Button>
    </form>
  )
}

function PasswordTab() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const changeMutation = useMutation({
    mutationFn: () =>
      usersApi.changePassword({ current_password: currentPassword, new_password: newPassword }),
    onSuccess: () => {
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      toast.success('Contraseña actualizada')
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || 'No se pudo cambiar la contraseña')
    },
  })

  const passwordsMatch = newPassword === confirmPassword
  const isValid = currentPassword.length >= 8 && newPassword.length >= 8 && passwordsMatch

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!isValid) {
      toast.error(
        !passwordsMatch
          ? 'Las contraseñas nuevas no coinciden'
          : 'Las contraseñas deben tener al menos 8 caracteres'
      )
      return
    }
    changeMutation.mutate()
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5 max-w-md">
      <div className="space-y-1.5">
        <Label htmlFor="current-password">Contraseña actual</Label>
        <Input
          id="current-password"
          type="password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          required
          autoComplete="current-password"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="new-password">Nueva contraseña</Label>
        <Input
          id="new-password"
          type="password"
          minLength={8}
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
          autoComplete="new-password"
          aria-describedby="new-password-help"
        />
        <p id="new-password-help" className="text-xs text-muted-foreground">
          Mínimo 8 caracteres.
        </p>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="confirm-password">Confirmar nueva contraseña</Label>
        <Input
          id="confirm-password"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          autoComplete="new-password"
          aria-invalid={confirmPassword.length > 0 && !passwordsMatch ? true : undefined}
        />
        {confirmPassword.length > 0 && !passwordsMatch && (
          <p className="text-xs text-destructive" role="alert">
            Las contraseñas no coinciden.
          </p>
        )}
      </div>

      <Button type="submit" disabled={changeMutation.isPending || !isValid}>
        {changeMutation.isPending ? 'Actualizando...' : 'Cambiar contraseña'}
      </Button>
    </form>
  )
}

function AppearanceTab() {
  const pref = useThemeStore((s) => s.pref)
  const setPref = useThemeStore((s) => s.setPref)

  const options: { value: ThemePref; label: string; icon: typeof Sun }[] = [
    { value: 'light',  label: 'Claro',          icon: Sun },
    { value: 'dark',   label: 'Oscuro',         icon: Moon },
    { value: 'system', label: 'Según sistema',  icon: Monitor },
  ]

  return (
    <div className="max-w-md">
      <fieldset>
        <legend className="text-sm font-semibold text-foreground mb-3">
          Tema de la interfaz
        </legend>
        <div className="grid grid-cols-3 gap-2">
          {options.map(({ value, label, icon: Icon }) => {
            const active = pref === value
            return (
              <button
                key={value}
                type="button"
                onClick={() => setPref(value)}
                aria-pressed={active}
                className={cn(
                  'flex flex-col items-center gap-2 px-3 py-4 rounded-lg border-2 transition-colors text-sm font-medium',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  active
                    ? 'border-primary bg-primary/10 text-primary-foreground text-primary'
                    : 'border-border bg-card text-foreground hover:border-border-strong'
                )}
              >
                <Icon className="w-5 h-5" aria-hidden="true" />
                {label}
              </button>
            )
          })}
        </div>
        <p className="text-xs text-muted-foreground mt-3">
          "Según sistema" sigue la preferencia de tu dispositivo y cambia automáticamente.
        </p>
      </fieldset>
    </div>
  )
}

export default function SettingsPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:px-6">
      <PageHeader
        title="Ajustes"
        subtitle="Administra tu perfil, contraseña y preferencias de visualización."
      />

      <Tabs defaultValue="profile" className="w-full">
        <TabsList className="w-full sm:w-auto overflow-x-auto">
          <TabsTrigger value="profile" className="gap-2">
            <UserIcon className="w-4 h-4" aria-hidden="true" />
            Perfil
          </TabsTrigger>
          <TabsTrigger value="password" className="gap-2">
            <Lock className="w-4 h-4" aria-hidden="true" />
            Contraseña
          </TabsTrigger>
          <TabsTrigger value="appearance" className="gap-2">
            <Palette className="w-4 h-4" aria-hidden="true" />
            Apariencia
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="bg-card border border-border rounded-xl p-6 mt-6">
          <ProfileTab />
        </TabsContent>
        <TabsContent value="password" className="bg-card border border-border rounded-xl p-6 mt-6">
          <PasswordTab />
        </TabsContent>
        <TabsContent value="appearance" className="bg-card border border-border rounded-xl p-6 mt-6">
          <AppearanceTab />
        </TabsContent>
      </Tabs>

      <p className="mt-6 text-xs text-muted-foreground flex items-center gap-1.5">
        <RefreshCw className="w-3 h-3" aria-hidden="true" />
        Los cambios se aplican inmediatamente. Algunos pueden requerir recargar la página.
      </p>
    </div>
  )
}
