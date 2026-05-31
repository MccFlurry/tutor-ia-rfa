# Reporte de Métricas Oficiales OE1 — Selección de LLM y Embeddings

**Proyecto:** Tutor IA Generativa — Curso Aplicaciones Móviles, IESTP "República Federal de Alemania" (Chiclayo)
**Tesista:** Roger Alessandro Zavaleta Marcelo · USAT — Escuela de Ingeniería de Sistemas y Computación
**Asesora:** Mg. Reyes Burgos, Karla
**Objetivo específico:** OE1 — Seleccionar el LLM de código abierto y el modelo de embeddings para generación y recuperación de respuestas en español del dominio de Aplicaciones Móviles.
**Fecha de corte:** 2026-05-29
**Versión:** 1.0

> Este reporte **complementa** `reporte-LLM.docx` (Sprint 2: comparativa de 3 LLM + 2 embeddings
> por rúbrica Likert, latencia y VRAM). Aquí se computan los **indicadores objetivamente
> verificables** del OE1 sobre los modelos seleccionados (`qwen2.5:7b-instruct-q4_K_M` +
> `mxbai-embed-large`) y el golden set de 50 ítems.

---

## 1. Resumen ejecutivo

El OE1 define indicadores objetivamente verificables en dos dimensiones: **generación** (calidad
de la respuesta del LLM) y **recuperación** (calidad del ranking del modelo de embeddings). Los
cinco indicadores se midieron sobre el modelo seleccionado en su configuración de producción y
sobre un golden set de 50 preguntas con respuesta de referencia.

| # | Dimensión | Indicador | Umbral | Valor medido | Veredicto |
|---|---|---|---|---|---|
| 1 | Generación | Accuracy | ≥0.70 | **0.72** | ✅ |
| 2 | Generación | Likert media | ≥4.0 | **4.325** | ✅ |
| 3 | Recuperación | Recall@5 | ≥0.70 | **0.72** | ✅ |
| 4 | Recuperación | MRR@10 | ≥0.65 | **0.684** | ✅ |
| 5 | Recuperación | nDCG@10 | ≥0.55 | **0.686** | ✅ |

**Resultado: 5 de 5 indicadores cumplen.** La generación queda validada por la consistencia
factual (Accuracy) y la calidad pedagógica (Likert) evaluadas por un juez independiente; la
recuperación queda validada por las tres métricas canónicas de ranking sobre el corpus del curso.
Ambas dimensiones del OE1 se consideran **validadas**.

---

## 2. Metodología

### 2.1 Golden set e infraestructura
- **50 preguntas con respuesta de referencia (ground_truth)**, módulos M1–M5
  (`backend/tests/fixtures/golden_set.json`).
- Modelos evaluados: generador **`qwen2.5:7b-instruct-q4_K_M`**, embeddings
  **`mxbai-embed-large`** (1024 dim), vía Ollama auto-hospedado (sin APIs pagas).
- Respuestas generadas con el **pipeline RAG de producción** (recuperación mxbai + **rerank
  cross-encoder** + generación qwen2.5, temperature 0.1, num_ctx 8192), configuración idéntica a
  `rag_service`. Esto mide el modelo en su configuración desplegada real.

### 2.2 Instrumento por indicador
| Indicador | Instrumento |
|---|---|
| Accuracy | juez **independiente** `llama3.1:8b` → consistencia factual (correcto/incorrecto) |
| Likert media | juez independiente `llama3.1:8b`, rúbrica 1–5 sobre 4 criterios |
| Recall@5 / MRR@10 / nDCG@10 | recuperación mxbai + rerank cross-encoder; relevancia binaria por keywords |

**Juez independiente** (`llama3.1:8b` ≠ generador `qwen2.5`): se evalúan las salidas del generador
con un modelo distinto para eliminar el sesgo de auto-preferencia (un modelo que se evalúa a sí
mismo tiende a inflar sus puntajes).

---

## 3. Resultados — generación (LLM seleccionado: qwen2.5)

| Indicador | Valor | Umbral | Veredicto |
|---|---|---|---|
| **Accuracy** | **0.72** (36/50) | ≥0.70 | ✅ |
| **Likert media** | **4.325** | ≥4.0 | ✅ |

Desglose Likert por criterio (juez `llama3.1`, escala 1–5): exactitud **3.90** · fluidez **4.60** ·
ausencia de alucinaciones **4.86** · pertinencia pedagógica **3.94**. El criterio de ausencia de
alucinaciones (4.86) confirma la fiabilidad del sistema RAG frente a la invención de información.

---

## 4. Resultados — recuperación (embeddings seleccionado: mxbai)

| Indicador | SIN rerank (coseno) | **CON rerank (producción)** | Umbral | Veredicto |
|---|---|---|---|---|
| Recall@5 | 0.62 | **0.72** | ≥0.70 | ✅ |
| MRR@10 | 0.535 | **0.684** | ≥0.65 | ✅ |
| nDCG@10 | 0.568 | **0.686** | ≥0.55 | ✅ |

La etapa de **rerank cross-encoder** (configuración de producción) eleva las tres métricas sobre su
umbral. Relevancia binaria: un chunk se considera relevante si contiene ≥2 de los
`expected_context_keywords` (substring, case-insensitive); 50 queries, pool de 30 candidatos.

Por módulo (con rerank): M1 Recall@5 **1.00** · M5 **0.90** · M4 **0.80** · M2 **0.62** ·
M3 **0.45** (UI, el más débil). El agregado cumple holgadamente; el módulo M3 se identifica como
oportunidad de mejora del corpus (densificación de contenido de interfaz de usuario).

> El índice pgvector está embebido con mxbai (1024 dim); `nomic-embed-text` (768 dim) no es
> comparable sin re-indexar y quedó descartado en el reporte comparativo del Sprint 2
> (Recall@5 0.35). La validación de recuperación es **consistente con OE2/RAGAS**:
> context_recall 0.812, context_precision 0.876 (instrumento ragas oficial).

---

## 5. Conclusiones

1. **Recuperación: CUMPLE** las tres métricas canónicas (Recall@5 0.72, MRR@10 0.684,
   nDCG@10 0.686) en la configuración de producción con rerank cross-encoder, de forma consistente
   con OE2/RAGAS. El modelo `mxbai-embed-large` queda validado para la tarea de recuperación
   semántica del dominio.
2. **Generación: CUMPLE** (Accuracy 0.72, Likert 4.325 con juez independiente). El LLM
   `qwen2.5:7b-instruct-q4_K_M` queda validado en corrección factual y calidad pedagógica.
3. **5/5 indicadores cumplen.** Las dos dimensiones centrales del OE1 —calidad de generación y
   precisión de recuperación— están validadas con instrumentos apropiados sobre la configuración
   desplegada real. **OE1 queda validado.**

Como continuidad de la evaluación (trabajo futuro) se propone una anotación multi-evaluador humana
sobre una submuestra del golden set, que complemente la evaluación automatizada con juez LLM.

---

## 6. Artefactos

- `backend/scripts/oe1_generation.py` · `oe1_retrieval.py` (harness reproducible).
- `docs/oe1_generation_results.json` · `oe1_retrieval_results.json` (resultados medidos).
- `docs/oe1_generation_log.jsonl` (50 respuestas + evaluaciones del juez independiente).
- Golden set: `backend/tests/fixtures/golden_set.json` (50 ítems M1–M5).
- Cross-referencia OE2: `docs/reporte-RAGAS.docx` (faithfulness 0.706, context_recall 0.812).

*Instrumentos reproducibles en el contenedor backend.*
