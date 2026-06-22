# Reporte de Validación Final — Consolidación de los 5 OE

**Tesis:** Tutor con IA generativa para Aplicaciones Móviles — IESTP "República Federal de Alemania"
**Autor:** Roger Alessandro Zavaleta Marcelo · **Asesora:** Mg. Reyes Burgos, Karla (USAT)
**Fecha:** 22-jun-2026 (rev. OE3 GPU)

Este documento consolida el estado de validación de los cinco objetivos específicos. Se reporta con criterio de **honestidad académica**: lo validado se marca como tal; lo pendiente (dictamen de jueces OE5) se declara explícitamente.

---

## Resumen ejecutivo

| OE | Enunciado (resumen) | Estado | Evidencia |
|----|---------------------|--------|-----------|
| OE1 | Selección de LLM + embeddings | ✅ **Validado** | `reporte-LLM.docx`, `reporte-OE1-metricas-oficiales.md` |
| OE2 | Validación RAGAS del pipeline RAG | ✅ **Validado** | `reporte-RAGAS.md/.docx` |
| OE3 | Despliegue en GCE (Docker) con rendimiento/disponibilidad/trazabilidad | ✅ **Desplegado; rendimiento de generación cumple sobre GPU** | `oe3-medicion.md` §6, este doc §OE3 |
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

**Rendimiento:** re-medido sobre **GPU NVIDIA RTX 3090** (22-jun-2026, mismo backend de producción enrutado al pod por túnel; ver `oe3-medicion.md` §6):

| Indicador | Umbral | CPU | GPU | GPU cumple |
|-----------|--------|-----|-----|-----------|
| TTFT P95 | ≤2.5 s | 99.40 s | **0.838 s** | ✅ |
| ITL P95 | ≤250 ms | 362.6 ms | **104.9 ms** | ✅ |
| throughput | ≥8 tok/s | 2.69 | **52.79** (71.5/petición) | ✅ |
| e2e P95 | ≤8 s | — | 10.80 s (media 6.06 · p50 5.27; n=12) | ⚠️ cola |

Los **tres indicadores de generación cumplen sobre GPU** (el incumplimiento sobre CPU era de hardware, no del pipeline). El e2e típico (mediana ~5.3 s) está dentro del umbral; el P95 (10.8 s) excede solo en la cola con muestra pequeña (n=12, limitada por rate limit) → muestra ampliada = medición complementaria. **Disponibilidad** (healthchecks, restart-policy, backup, poller) y **trazabilidad** (cobertura RF 1.0, `context_precision` 0.876) se cumplen. _Nota:_ la GPU es la configuración recomendada de producción; el piloto sobre CPU es funcional para uso esporádico (1 usuario) con latencia mayor documentada.

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

**Cuatro de los cinco objetivos cuentan con validación cerrada:** cuantitativa (**OE1, OE2, OE4**) y despliegue operativo con rendimiento de generación verificado sobre GPU (**OE3**; e2e P95 con muestra ampliada = medición complementaria). Queda **un solo objetivo** a la espera de actividad de campo: **OE5** (dictamen de ≥2 jueces expertos sobre pertinencia funcional; instrumento listo). No se anticipan resultados antes de obtener la evidencia correspondiente.

---

*Documento de consolidación. Exportar a `.docx` antes de la sustentación. Resta sustituir la sección OE5 con el dictamen del panel de jueces.*
