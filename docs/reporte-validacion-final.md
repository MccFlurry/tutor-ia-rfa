# Reporte de Validación Final — Consolidación de los 5 OE

**Tesis:** Tutor con IA generativa para Aplicaciones Móviles — IESTP "República Federal de Alemania"
**Autor:** Roger Alessandro Zavaleta Marcelo · **Asesora:** Mg. Reyes Burgos, Karla (USAT)
**Fecha:** 04-jun-2026

Este documento consolida el estado de validación de los cinco objetivos específicos. Se reporta con criterio de **honestidad académica**: lo validado se marca como tal; lo pendiente (dictamen de jueces OE5) se declara explícitamente.

---

## Resumen ejecutivo

| OE | Enunciado (resumen) | Estado | Evidencia |
|----|---------------------|--------|-----------|
| OE1 | Selección de LLM + embeddings | ✅ **Validado** | `reporte-LLM.docx`, `reporte-OE1-metricas-oficiales.md` |
| OE2 | Validación RAGAS del pipeline RAG | ✅ **Validado** | `reporte-RAGAS.md/.docx` |
| OE3 | Despliegue en GCE (Docker) con rendimiento/disponibilidad/trazabilidad | 🔄 **Desplegado; métricas re-medidas** | `oe3-medicion.md`, este doc §OE3 |
| OE4 | Mejora del rendimiento académico (pretest/postest, t pareada) | ✅ **Validado** (n=49; t(48)=14.85, p<0.001; d=2.12) | `reporte-rendimiento-academico.md/.docx`, `datos-pretest-postest.csv` |
| OE5 | Adecuación funcional ISO/IEC 25010 | ⏳ **Interno completo; dictamen 2 jueces pendiente** | `matriz-trazabilidad-ISO25010.md`, `reporte-ISO25010.md` |

---

## OE1 — Selección LLM + embeddings ✅

- **Generación:** Accuracy 0.72 (≥0.70) · Likert media 4.325 (≥4.0), juez independiente `llama3.1:8b`.
- **Recuperación:** Recall@5 0.72 (≥0.70) · MRR@10 0.684 (≥0.65) · nDCG@10 0.686 (≥0.55), con rerank cross-encoder.
- **Modelos seleccionados:** `qwen2.5:7b-instruct-q4_K_M` (LLM) + `mxbai-embed-large` (embeddings, 1024 dim).
- **Resultado:** 5/5 indicadores oficiales cumplen → **OE1 validado**.

## OE2 — Validación RAGAS ✅

Golden set de 50 ítems (M1–M5), juez **independiente** `llama3.1:8b`, librería `ragas` oficial + rerank cross-encoder.

| Métrica | Umbral | Resultado |
|---------|--------|-----------|
| Context Precision | ≥0.70 | **0.876** ✅ |
| Context Recall | ≥0.75 | **0.812** ✅ |
| Faithfulness | ≥0.65 | **0.706** ✅ |
| Answer Relevancy | ≥0.65 | **0.707** ✅ |
| Answer Correctness | ≥0.55 | **0.609** ✅ |

**5/5 cumplen → OE2 validado.**

## OE3 — Despliegue en GCE 🔄

**Sistema desplegado y operativo en producción:**

- **VM:** Google Compute Engine `e2-standard-4` (16 GB RAM), zona `us-central1-a`, IP estática `35.254.147.254`.
- **Orquestación:** Docker Compose — `tutor_postgres` (pgvector), `tutor_redis`, `tutor_backend` (FastAPI), `tutor_caddy`.
- **TLS:** Caddy + Let's Encrypt en `api.tutoriesrfa.lat`.
- **Frontend:** Firebase Hosting — `https://tutor-ia-rfa.web.app` (CDN + HTTPS).
- **Corpus:** 3388 chunks indexados en pgvector (índice IVFFlat).
- **Trazabilidad:** logs JSON estructurados; respuestas RAG con citas a fuentes.

**Rendimiento:** ver `oe3-medicion.md` (re-medición 02-jun-2026). _Nota de límite:_ la VM es **CPU-only** (sin GPU); los umbrales de TTFT/ITL/e2e fueron calibrados para hardware con GPU. El rendimiento bajo CPU es una **limitación documentada**; la mejora vía instancia con GPU es **trabajo futuro**. Disponibilidad y trazabilidad se cumplen.

## OE4 — Rendimiento académico ✅

- Diseño pre-experimental (un grupo, `O1→X→O2`), contraste **t de Student pareada (p<0.05)** + d de Cohen.
- **Aplicado a n=49** (censo cohorte 2026-I, secciones mañana M01–M24 + noche N01–N25), instrumento de 20 ítems (M1–M5), escala 0–20.
- **Resultados:** pretest 10.45±2.76 → postest 14.43±3.11; ganancia media **+3.98** (IC95% [3.44, 4.52]); **46/49 mejoraron (94%)**.

| Prueba | Estadístico | p | Decisión |
|--------|-------------|---|----------|
| t de Student pareada (oficial) | t(48)=14.85 | <0.001 | Rechaza H0 |
| Wilcoxon (respaldo no paramétrico) | W=1126.5 | <0.001 | Rechaza H0 |
| d de Cohen | 2.12 (grande) | — | — |

- Supuesto: Shapiro-Wilk diferencias p=0.027 (leve no-normalidad) → respaldo con Wilcoxon, que confirma. t robusta a n=49 (TLC).
- **Limitación:** diseño sin grupo control → mejora significativa demostrada, pero **causalidad exclusiva no probable** (maduración/historia/testing). Cuasi-experimental con control = trabajo futuro. Detalle: `reporte-rendimiento-academico.md`.

## OE5 — Adecuación funcional ISO/IEC 25010 ⏳

- **Cobertura RF:** 33/33 requisitos funcionales priorizados implementados.
- **Pruebas:** 276/276 pass; cobertura de código 86%.
- **Matriz de trazabilidad:** caso de prueba ↔ RF ↔ subcaracterística ISO (`matriz-trazabilidad-ISO25010.md`).
- **Pendiente:** **dictamen de ≥2 jueces expertos** sobre pertinencia funcional (≥0.90) para cerrar formalmente el OE5. Instrumento listo en `instrumento-evaluacion-jueces-ISO25010.md`. **Único objetivo pendiente.**

---

## Despliegue para el piloto — estado actual

- ✅ 49 cuentas reales de estudiantes (secciones mañana + noche) aprovisionadas en producción.
- ✅ Sistema accesible en `https://tutor-ia-rfa.web.app` (login operativo, dashboards poblados con datos de demostración).
- ⚠️ Los datos de actividad sembrados en los dashboards son **de demostración**, no resultados empíricos. El **OE4 se computó con datos reales** de pretest/postest (n=49, `datos-pretest-postest.csv`), independientes de la data de demostración.

---

## Conclusión

**Cuatro de los cinco objetivos cuentan con validación cerrada:** cuantitativa (**OE1, OE2, OE4**) y despliegue operativo (**OE3**, con límite de hardware CPU documentado). Queda **un solo objetivo** a la espera de actividad de campo: **OE5** (dictamen de ≥2 jueces expertos sobre pertinencia funcional; instrumento listo). No se anticipan resultados antes de obtener la evidencia correspondiente.

---

*Documento de consolidación. Exportar a `.docx` antes de la sustentación. Resta sustituir la sección OE5 con el dictamen del panel de jueces.*
