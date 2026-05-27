import { useParams } from 'react-router-dom'

export default function AdminStudentReportPage() {
  const { userId } = useParams<{ userId: string }>()

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 sm:px-6">
      <header className="mb-6">
        <h1 className="text-2xl font-extrabold text-foreground">
          Reporte de Estudiante
        </h1>
        <p className="text-sm text-muted-foreground">ID: {userId}</p>
      </header>
      <div className="p-12 text-center text-muted-foreground border border-dashed border-border rounded-xl">
        Contenido en construcción — ver Task 15.
      </div>
    </div>
  )
}
