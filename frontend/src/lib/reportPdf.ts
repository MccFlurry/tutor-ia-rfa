import type { AIReport, StudentDetail } from '@/types/adminReports'

const LEVEL_LABEL: Record<string, string> = {
  beginner: 'Principiante',
  intermediate: 'Intermedio',
  advanced: 'Avanzado',
}

const RISK_LABEL: Record<string, string> = {
  bajo: 'Bajo',
  medio: 'Medio',
  alto: 'Alto',
}

const RISK_COLOR: Record<string, string> = {
  bajo: '#16a34a',
  medio: '#d97706',
  alto: '#b91c1c',
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function mdLite(raw: string): string {
  const safe = escapeHtml(raw)
  const inline = safe
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
  return inline
    .split(/\n{2,}/)
    .map((p) => `<p>${p.replace(/\n/g, '<br>')}</p>`)
    .join('')
}

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('es-PE', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit',
    })
  } catch { return iso }
}

function fmtDay(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleDateString('es-PE', {
      year: 'numeric', month: 'long', day: 'numeric',
    })
  } catch { return iso }
}

function levelLabel(l: string | null | undefined): string {
  return l ? (LEVEL_LABEL[l] ?? l) : 'sin asignar'
}

function buildCover(detail: StudentDetail): string {
  const today = fmtDay(new Date().toISOString())
  const lvl = levelLabel(detail.level)
  return `
    <section class="pdf-cover" style="page-break-after: always;">
      <div class="cover-bar"></div>
      <img src="/logo-iestp-rfa.png" alt="" class="cover-logo" crossorigin="anonymous" />
      <div class="cover-eyebrow">IESTP "República Federal de Alemania" · Chiclayo</div>
      <h1 class="cover-title">Reporte de Estudiante</h1>
      <div class="cover-sub">Tutor IA — Aplicaciones Móviles</div>

      <div class="cover-card">
        <div class="cover-row"><span>Estudiante</span><strong>${escapeHtml(detail.full_name)}</strong></div>
        <div class="cover-row"><span>Correo</span><strong>${escapeHtml(detail.email)}</strong></div>
        <div class="cover-row"><span>Nivel actual</span><strong>${escapeHtml(lvl)}</strong></div>
        <div class="cover-row"><span>Progreso global</span><strong>${detail.overall_progress_pct.toFixed(0)}%</strong></div>
        <div class="cover-row"><span>Última actividad</span><strong>${escapeHtml(fmtDate(detail.last_activity_at))}</strong></div>
        <div class="cover-row"><span>Fecha de emisión</span><strong>${escapeHtml(today)}</strong></div>
      </div>

      <div class="cover-sign">
        <div class="sign-block">
          <div class="sign-line"></div>
          <div class="sign-label">Docente / Coordinador</div>
        </div>
        <div class="sign-block">
          <div class="sign-line"></div>
          <div class="sign-label">Sello institucional</div>
        </div>
      </div>

      <div class="cover-foot">Documento generado automáticamente por el Sistema Tutor IA RFA · uso académico.</div>
    </section>
  `
}

function buildKpis(detail: StudentDetail): string {
  const cells = [
    { label: 'Progreso global', value: `${detail.overall_progress_pct.toFixed(0)}%` },
    { label: 'Tiempo invertido', value: `${Math.round(detail.total_time_seconds / 60)} min` },
    { label: 'Mensajes al tutor', value: detail.chat_messages_count.toString() },
    { label: 'Logros obtenidos', value: detail.achievements_earned.length.toString() },
  ]
  return `
    <section class="pdf-section avoid-break">
      <h2>Resumen general</h2>
      <div class="kpi-grid">
        ${cells.map(c => `
          <div class="kpi">
            <div class="kpi-label">${escapeHtml(c.label)}</div>
            <div class="kpi-value">${escapeHtml(c.value)}</div>
          </div>`).join('')}
      </div>
    </section>
  `
}

function buildModules(detail: StudentDetail): string {
  if (!detail.modules.length) return ''
  const rows = detail.modules.map(m => {
    const pct = Math.max(0, Math.min(100, m.progress_pct))
    const quiz = m.avg_quiz_score !== null ? `${(m.avg_quiz_score * 100).toFixed(0)}%` : '—'
    const code = m.avg_coding_score !== null ? m.avg_coding_score.toFixed(0) : '—'
    return `
      <div class="mod-row avoid-break">
        <div class="mod-head">
          <strong>${escapeHtml(m.module_title)}</strong>
          <span>${m.topics_completed}/${m.topics_total} temas</span>
        </div>
        <div class="bar"><div class="bar-fill" style="width:${pct}%"></div></div>
        <div class="mod-meta">
          <span>Quiz: <strong>${quiz}</strong></span>
          <span>Coding: <strong>${code}</strong></span>
          <span>Progreso: <strong>${pct.toFixed(0)}%</strong></span>
        </div>
      </div>`
  }).join('')
  return `
    <section class="pdf-section">
      <h2>Progreso por módulo</h2>
      ${rows}
    </section>
  `
}

function buildRecent(detail: StudentDetail): string {
  const quizRows = detail.recent_quizzes.slice(0, 10).map(q => `
    <tr>
      <td>${escapeHtml(q.topic_title)}</td>
      <td class="num">${(q.score * 100).toFixed(0)}%</td>
      <td class="num">${escapeHtml(fmtDate(q.attempted_at))}</td>
    </tr>`).join('') || `<tr><td colspan="3" class="empty">Sin registros.</td></tr>`

  const codeRows = detail.recent_coding.slice(0, 10).map(c => `
    <tr>
      <td>${escapeHtml(c.challenge_title)}</td>
      <td class="num">${c.score.toFixed(0)}/100</td>
      <td class="num">${escapeHtml(fmtDate(c.submitted_at))}</td>
    </tr>`).join('') || `<tr><td colspan="3" class="empty">Sin registros.</td></tr>`

  return `
    <section class="pdf-section">
      <h2>Actividad reciente</h2>
      <h3>Últimos quizzes</h3>
      <table class="pdf-table">
        <thead><tr><th>Tema</th><th class="num">Puntaje</th><th class="num">Fecha</th></tr></thead>
        <tbody>${quizRows}</tbody>
      </table>
      <h3 style="margin-top:10px;">Últimos desafíos de código</h3>
      <table class="pdf-table">
        <thead><tr><th>Desafío</th><th class="num">Puntaje</th><th class="num">Fecha</th></tr></thead>
        <tbody>${codeRows}</tbody>
      </table>
    </section>
  `
}

function buildLevelHistory(detail: StudentDetail): string {
  if (!detail.level_history.length) return ''
  const rows = detail.level_history.map(h => `
    <tr>
      <td>${escapeHtml(fmtDate(h.changed_at))}</td>
      <td><strong>${escapeHtml(levelLabel(h.level))}</strong></td>
      <td class="num">${h.score.toFixed(0)}</td>
      <td>${escapeHtml(h.reason ?? '—')}</td>
    </tr>`).join('')
  return `
    <section class="pdf-section avoid-break">
      <h2>Historial de nivel</h2>
      <table class="pdf-table">
        <thead><tr><th>Fecha</th><th>Nivel</th><th class="num">Puntaje</th><th>Motivo</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </section>
  `
}

function buildAchievements(detail: StudentDetail): string {
  if (!detail.achievements_earned.length) return ''
  const items = detail.achievements_earned.map(a =>
    `<li><span class="badge-emoji">${escapeHtml(a.badge_emoji)}</span> <strong>${escapeHtml(a.name)}</strong> <span class="muted">(${escapeHtml(fmtDate(a.earned_at))})</span></li>`
  ).join('')
  return `
    <section class="pdf-section avoid-break">
      <h2>Logros obtenidos</h2>
      <ul class="ach-list">${items}</ul>
    </section>
  `
}

function buildAIReport(report: AIReport): string {
  const color = RISK_COLOR[report.risk_level] ?? '#525252'
  const riskTxt = RISK_LABEL[report.risk_level] ?? report.risk_level
  return `
    <section class="pdf-section ai-block">
      <h2>Reporte IA</h2>
      <div class="risk-chip" style="background:${color}1a;color:${color};border:1px solid ${color}66;">
        Riesgo: <strong style="margin-left:4px;">${escapeHtml(riskTxt)}</strong>
      </div>
      <div class="ai-summary">${mdLite(report.summary)}</div>
      <p class="ai-reason"><strong>Justificación:</strong> ${escapeHtml(report.risk_reason)}</p>

      <h3>Fortalezas</h3>
      <ul>${report.strengths.map(s => `<li>${escapeHtml(s)}</li>`).join('')}</ul>

      <h3>Debilidades</h3>
      <ul>${report.weaknesses.map(s => `<li>${escapeHtml(s)}</li>`).join('')}</ul>

      <h3>Intervenciones sugeridas</h3>
      <ul>${report.interventions.map(s => `<li>${escapeHtml(s)}</li>`).join('')}</ul>

      <p class="ai-foot muted">Generado el ${escapeHtml(fmtDate(report.generated_at))}${report.cached ? ' (caché)' : ''}.</p>
    </section>
  `
}

const PDF_CSS = `
  .pdf-root { font-family: 'Helvetica', 'Arial', sans-serif; color: #1f2937; font-size: 11pt; line-height: 1.45; }
  .pdf-root * { box-sizing: border-box; }
  .pdf-root h1, .pdf-root h2, .pdf-root h3 { color: #0f172a; margin: 0 0 8px; }
  .pdf-root h2 { font-size: 14pt; border-bottom: 2px solid #1d4ed8; padding-bottom: 4px; margin-top: 14px; }
  .pdf-root h3 { font-size: 11.5pt; margin-top: 8px; }
  .pdf-root p { margin: 4px 0; }
  .pdf-root ul { margin: 4px 0 8px 18px; padding: 0; }
  .pdf-root li { margin: 2px 0; }
  .muted { color: #6b7280; font-size: 9.5pt; }

  /* Cover */
  .pdf-cover { position: relative; padding: 80px 0 0; text-align: center; min-height: 980px; }
  .cover-bar { position: absolute; top:0; left:-40px; right:-40px; height: 14px; background: linear-gradient(90deg,#1d4ed8 0%, #0ea5e9 50%, #f59e0b 100%); }
  .cover-logo { width: 120px; height: 120px; object-fit: contain; margin: 0 auto 16px; display: block; }
  .cover-eyebrow { font-size: 10.5pt; letter-spacing: 0.06em; text-transform: uppercase; color: #475569; }
  .cover-title { font-size: 30pt; font-weight: 800; color: #0f172a; margin: 18px 0 4px; letter-spacing: -0.01em; }
  .cover-sub { font-size: 13pt; color: #1d4ed8; font-weight: 600; margin-bottom: 32px; }
  .cover-card { margin: 0 60px; padding: 18px 22px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; text-align: left; }
  .cover-row { display: flex; justify-content: space-between; gap: 12px; padding: 6px 0; border-bottom: 1px dashed #e2e8f0; font-size: 11pt; }
  .cover-row:last-child { border-bottom: none; }
  .cover-row span { color: #64748b; }
  .cover-row strong { color: #0f172a; font-weight: 600; }
  .cover-sign { display: flex; justify-content: space-around; margin: 60px 40px 0; }
  .sign-block { width: 200px; text-align: center; }
  .sign-line { border-top: 1px solid #94a3b8; margin-bottom: 6px; height: 32px; }
  .sign-label { font-size: 9.5pt; color: #64748b; }
  .cover-foot { position: absolute; bottom: 24px; left: 0; right: 0; font-size: 9pt; color: #94a3b8; }

  /* Sections */
  .pdf-section { margin: 8px 0 14px; }
  .avoid-break { page-break-inside: avoid; }

  .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
  .kpi { border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px; background: #f8fafc; }
  .kpi-label { font-size: 8.5pt; text-transform: uppercase; letter-spacing: 0.04em; color: #64748b; }
  .kpi-value { font-size: 16pt; font-weight: 700; color: #0f172a; margin-top: 2px; }

  .mod-row { padding: 8px 10px; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 6px; background: #fff; }
  .mod-head { display: flex; justify-content: space-between; font-size: 10.5pt; margin-bottom: 4px; }
  .mod-head span { color: #64748b; }
  .bar { height: 8px; background: #e2e8f0; border-radius: 999px; overflow: hidden; }
  .bar-fill { height: 100%; background: linear-gradient(90deg,#1d4ed8,#3b82f6); }
  .mod-meta { display: flex; gap: 14px; font-size: 9.5pt; color: #475569; margin-top: 4px; }

  .pdf-table { width: 100%; border-collapse: collapse; font-size: 10pt; }
  .pdf-table th, .pdf-table td { padding: 5px 8px; border-bottom: 1px solid #e2e8f0; text-align: left; }
  .pdf-table th { background: #f1f5f9; color: #334155; font-weight: 600; font-size: 9.5pt; text-transform: uppercase; letter-spacing: 0.03em; }
  .pdf-table td.num, .pdf-table th.num { text-align: right; font-variant-numeric: tabular-nums; }
  .pdf-table .empty { text-align: center; color: #94a3b8; font-style: italic; }

  .ach-list { list-style: none; margin: 0; padding: 0; }
  .ach-list li { padding: 4px 0; border-bottom: 1px dashed #e2e8f0; }
  .badge-emoji { font-size: 12pt; margin-right: 4px; }

  .ai-block { background: #fafbff; border: 1px solid #dbeafe; border-radius: 10px; padding: 12px 14px; }
  .risk-chip { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 9.5pt; margin-bottom: 8px; }
  .ai-summary { margin: 4px 0 8px; }
  .ai-reason { font-size: 10.5pt; color: #334155; }
  .ai-foot { margin-top: 10px; font-size: 9pt; }
`

function buildRoot(detail: StudentDetail, report: AIReport | null): HTMLElement {
  const wrap = document.createElement('div')
  wrap.className = 'pdf-root'
  wrap.style.cssText = 'width: 794px; padding: 28px 40px; background: #fff;'
  wrap.innerHTML = `
    <style>${PDF_CSS}</style>
    ${buildCover(detail)}
    ${buildKpis(detail)}
    ${buildModules(detail)}
    ${buildRecent(detail)}
    ${buildLevelHistory(detail)}
    ${buildAchievements(detail)}
    ${report ? buildAIReport(report) : ''}
  `
  return wrap
}

function sanitizeFilename(s: string): string {
  return s.normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-zA-Z0-9_-]+/g, '_').replace(/^_+|_+$/g, '') || 'estudiante'
}

export async function generateReportPDF(
  detail: StudentDetail,
  report: AIReport | null,
): Promise<void> {
  const root = buildRoot(detail, report)
  const hidden = document.createElement('div')
  hidden.style.cssText = 'position:fixed;left:-10000px;top:0;z-index:-1;'
  hidden.appendChild(root)
  document.body.appendChild(hidden)

  const today = new Date().toISOString().slice(0, 10)
  const filename = `reporte_${sanitizeFilename(detail.full_name)}_${today}.pdf`

  try {
    const { default: html2pdf } = await import('html2pdf.js')
    const worker = html2pdf().set({
      margin: [16, 14, 20, 14],
      filename,
      image: { type: 'jpeg', quality: 0.96 },
      html2canvas: { scale: 2, useCORS: true, backgroundColor: '#ffffff' },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
      pagebreak: { mode: ['css', 'legacy'], avoid: '.avoid-break, .mod-row, .kpi, table tr' },
    }).from(root)

    await worker
      .toPdf()
      .get('pdf')
      .then((pdf: any) => {
        const total = pdf.internal.getNumberOfPages()
        const w = pdf.internal.pageSize.getWidth()
        const h = pdf.internal.pageSize.getHeight()
        const today2 = new Date().toLocaleDateString('es-PE')
        for (let i = 2; i <= total; i++) {
          pdf.setPage(i)
          pdf.setDrawColor(29, 78, 216)
          pdf.setLineWidth(0.4)
          pdf.line(14, 12, w - 14, 12)
          pdf.setFontSize(8)
          pdf.setTextColor(71, 85, 105)
          pdf.text('Tutor IA — IESTP RFA · Aplicaciones Móviles', 14, 9)
          pdf.text(detail.full_name, w - 14, 9, { align: 'right' })
          pdf.setDrawColor(226, 232, 240)
          pdf.line(14, h - 12, w - 14, h - 12)
          pdf.text(`Emitido ${today2}`, 14, h - 7)
          pdf.text(`Página ${i} de ${total}`, w - 14, h - 7, { align: 'right' })
        }
        return pdf
      })
      .save()
  } finally {
    document.body.removeChild(hidden)
  }
}
