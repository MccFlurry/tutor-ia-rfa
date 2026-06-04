# Índice del Bundle — Entregables para el Informe Final

**Tesis:** Tutor con IA generativa para Aplicaciones Móviles — IESTP "República Federal de Alemania" (Chiclayo)
**Autor (tesista):** Roger Alessandro Zavaleta Marcelo · **Asesora:** Mg. Reyes Burgos, Karla (USAT)
**Generado:** 2026-06-04

> Carpeta de **verificación + carga**. Contiene copias `.docx` de los entregables mapeados a los 5 objetivos específicos, ordenadas para alimentar al proyecto en Claude que redactará el informe final. Revisa cada archivo; al subirlos, **indica explícitamente a Claude qué resultados están pendientes** (ver §Estado honesto).

---

## Contenido de la carpeta

| # | Archivo | OE | Estado |
|---|---------|----|--------|
| 00 | `00-INDICE.docx` | — | este índice |
| 01 | `01-ERS.docx` | base | ✅ Especificación de requisitos (52 RF / 33 priorizados) |
| 02 | `02-OE1-reporte-LLM.docx` | OE1 | ✅ Comparativa LLM + embeddings → qwen2.5 + mxbai |
| 03 | `03-OE1-metricas-oficiales.docx` | OE1 | ✅ Indicadores oficiales (Accuracy 0.72, Likert 4.325, Recall@5 0.72…) |
| 04 | `04-OE2-reporte-RAGAS.docx` | OE2 | ✅ RAGAS 5/5 (precision 0.876, recall 0.812, faithfulness 0.706…) |
| 05 | `05-OE3-arquitectura.docx` | OE3 | 🔄 Arquitectura + stack + despliegue C4 |
| 06 | `06-OE3-medicion.docx` | OE3 | 🔄 Medición rendimiento (limitación CPU sin GPU, documentada) |
| 07 | `07-OE4-instrumento-pretest-postest.docx` | OE4 | ⏳ Instrumento 20 ítems (listo) |
| 08 | `08-OE4-clave-correccion.docx` | OE4 | ⏳ Clave de corrección |
| 09 | `09-OE4-reporte-rendimiento-academico.docx` | OE4 | ✅ **Resultados reales** (n=49): t(48)=14.85, p<0.001, d=2.12 |
| 10 | `10-OE5-matriz-trazabilidad-ISO25010.docx` | OE5 | ✅ Matriz 33 RF → endpoint → test (396 tests, 88%) |
| 11 | `11-OE5-reporte-ISO25010.docx` | OE5 | ✅ Completitud 1.00 + corrección 1.00 formalizadas |
| 12 | `12-OE5-instrumento-jueces.docx` | OE5 | ⏳ Instrumento de jueces (listo); **dictamen ≥2 jueces pendiente** |
| 13 | `13-consolidacion-validacion-final.docx` | — | Consolidación honesta de los 5 OE |

---

## Estado honesto por OE (léelo antes de redactar)

| OE | Qué afirma | Qué NO afirmar todavía |
|----|-----------|------------------------|
| **OE1** | LLM + embeddings seleccionados y validados (5/5 indicadores). | — |
| **OE2** | Pipeline RAG validado con RAGAS (5/5). | — |
| **OE3** | Sistema **desplegado y operativo** en GCE (Docker + Caddy + Firebase); disponibilidad y trazabilidad cumplen. | Que el **rendimiento** cumple umbrales: la VM es **CPU sin GPU** (TTFT/throughput no cumplen) → declarar como **limitación documentada + trabajo futuro (GPU)**. |
| **OE4** | **Validado con datos reales (n=49):** pretest 10.45 → postest 14.43; t pareada t(48)=14.85, **p<0.001**, Cohen's **d=2.12 (grande)**; Wilcoxon de respaldo p<0.001. | Que la mejora prueba **causalidad exclusiva** del tutor: diseño **sin grupo control** → reportar como **limitación** (maduración/historia/testing); cuasi-experimental con control = trabajo futuro. |
| **OE5** | **Completitud (X=1.00 ≥0.95)** y **corrección (X=1.00 ≥0.90)** formalizadas con 396 tests (0 fallos), 88% cobertura. | **Pertinencia funcional (≥0.90)**: requiere **dictamen de ≥2 jueces expertos** (instrumento #12 listo, en blanco). No simular valores. |

**Regla de integridad:** los datos de actividad *de demo* en los dashboards de producción son **DEMO**, nunca evidencia. El OE4 se computó con datos reales de pretest/postest (`datos-pretest-postest.csv`, n=49), **independientes** de la demo. No inventar el dictamen de jueces (OE5).

---

## Lo que falta para cerrar (1 pendiente real)

1. **OE5 — dictamen de jueces.** 2 expertos (p. ej. asesora + 1 ingeniero/docente del área) llenan y firman el instrumento #12 → pertinencia funcional ≥0.90. **No bloqueado por calendario** — el sistema ya está terminado.

> OE1, OE2 y **OE4** validados cuantitativamente; OE3 desplegado (límite CPU documentado). Solo resta el panel de jueces (OE5).

---

## Excluido a propósito de esta carpeta

- **Hojas de examen personalizadas de los 49 estudiantes** (`examen-pretest-postest-hojas.docx`) — contienen **datos personales (PII)**; se mantienen fuera del bundle e ignoradas por git. No subir a servicios externos.
- Datos `datos-pretest-postest.csv` (n=49, **sin PII** — solo códigos M01–N25 + puntajes) viven en `docs/`; insumo del análisis OE4.

---

## Cómo usar con tu proyecto en Claude

1. Sube los archivos `01`–`13` (y este índice) al proyecto.
2. Pega en las instrucciones del proyecto el bloque **«Estado honesto por OE»** de arriba.
3. Pide el informe final con **OE1–OE4 como resultados consumados**; solo **OE5 (dictamen jueces)** va como *método listo + pendiente de aplicación*.
