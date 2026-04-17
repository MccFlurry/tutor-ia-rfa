export default function Footer() {
  const year = new Date().getFullYear()
  return (
    <footer
      role="contentinfo"
      className="border-t border-gray-200 bg-white px-4 py-4 sm:px-6 text-xs text-gray-500 flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:justify-between"
    >
      <p>
        © {year}{' '}
        <span className="font-semibold text-institutional-700">
          IESTP "República Federal de Alemania"
        </span>{' '}
        — Chiclayo, Perú
      </p>
      <p className="text-gray-400">
        Tesis USAT · Sistema de Tutoría Inteligente con IA Generativa
      </p>
    </footer>
  )
}
