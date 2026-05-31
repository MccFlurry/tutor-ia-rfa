# Reporte de Métricas Oficiales OE1 — Selección de LLM y Embeddings

**Proyecto:** Tutor IA Generativa — Curso Aplicaciones Móviles, IESTP "República Federal de Alemania" (Chiclayo)
**Tesista:** Roger Alessandro Zavaleta Marcelo · USAT — Escuela de Ingeniería de Sistemas y Computación
**Asesora:** Mg. Reyes Burgos, Karla
**Objetivo específico:** OE1 — Seleccionar el LLM de código abierto y el modelo de embeddings para generación y recuperación de respuestas en español del dominio de Aplicaciones Móviles.
**Fecha de corte:** 2026-05-29
**Versión:** 1.0

> Este reporte **complementa** `reporte-LLM.docx` (Sprint 2: comparativa de 3 LLM + 2 embeddings
> por rúbrica Likert, latencia, VRAM). Aquí se computan los **indicadores objetivamente
> verificables oficiales** del OE1 que no figuraban en aquel reporte, sobre el modelo
> seleccionado (`qwen2.5:7b-instruct-q4_K_M` + `mxbai-embed-large`) y el golden set de 50 ítems.

---

## 1. Resumen ejecutivo — tablero de los 9 indicadores

| # | Indicador | Tipo | Umbral | Valor medido | Veredicto |
|---|---|---|---|---|---|
| 1 | ROUGE-L (F1) | generación | ≥0.35 | **0.171** | ❌ |
| 2 | BLEU | generación | ≥0.25 | **0.059** | ❌ |
| 3 | Accuracy | generación | ≥0.70 | **0.72** | ✅ |
| 4 | Likert media | generación | ≥4.0 | **4.325** | ✅ |
| 5 | Cohen's κ (inter-juez) | fiabilidad | ≥0.60 | **0.211** (Likert) / **0.239** (binario) | ❌ |
| 6 | Recall@5 | recuperación | ≥0.70 | **0.72** | ✅ |
| 7 | MRR@10 | recuperación | ≥0.65 | **0.684** | ✅ |
| 8 | nDCG@10 | recuperación | ≥0.55 | **0.686** | ✅ |
| 9 | Spearman STS | recuperación | ≥0.70 | **0.664** | ❌ |

**Resultado: 5 de 9 indicadores cumplen.** Cumplen las métricas **semánticas de generación**
(Accuracy, Likert) y **las tres métricas canónicas de recuperación** (Recall@5, MRR@10, nDCG@10).
Quedan por debajo cuatro: las dos métricas de **solapamiento n-gram** (ROUGE-L, BLEU), la
**concordancia κ inter-juez**, y la **STS general de dominio abierto**. La §6 argumenta que esos
cuatro reflejan **inadecuación del instrumento a la tarea**, no deficiencia del sistema, y se
apoya en evidencia convergente (Accuracy 0.72, Likert 4.325, y las métricas RAGAS de OE2).

---

## 2. Metodología

### 2.1 Golden set e infraestructura
- **50 preguntas con ground_truth**, módulos M1–M5 (`backend/tests/fixtures/golden_set.json`).
- Modelos: generador **`qwen2.5:7b-instruct-q4_K_M`**, embeddings **`mxbai-embed-large`** (1024 dim),
  vía Ollama auto-hospedado (sin APIs pagas).
- Respuestas generadas con el **pipeline RAG de producción** (recuperación mxbai + **rerank
  cross-encoder** + generación qwen2.5, temperature 0.1, num_ctx 8192), config idéntica a
  `rag_service`. Esto mide al LLM en su configuración desplegada real.

### 2.2 Instrumento por métrica
| Métrica | Instrumento |
|---|---|
| ROUGE-L (F1) | `rouge_score` (sin stemmer; español), answer vs ground_truth |
| BLEU | `sacrebleu` corpus-BLEU, tokenize=`intl`, answer vs ground_truth |
| Accuracy | juez **independiente** `llama3.1:8b` → consistencia factual (correcto/incorrecto) |
| Likert media | juez independiente `llama3.1:8b`, rúbrica 1-5 sobre 4 criterios |
| Cohen's κ | concordancia **inter-juez** `llama3.1` vs `llama3` sobre el Likert global (κ cuadrático) |
| Recall@5 / MRR@10 / nDCG@10 | recuperación mxbai + rerank; relevancia binaria por keywords |
| Spearman STS | `stsb_multi_mt` (config `es`, 1379 pares); coseno mxbai vs gold humano 0-5 |

**Juez independiente** (`llama3.1:8b` ≠ generador `qwen2.5`): elimina el sesgo de
auto-preferencia (defecto del reporte-LLM original, que usó qwen2.5 como juez de sí mismo).

---

## 3. Resultados — generación (LLM seleccionado: qwen2.5)

| Métrica | Valor | Umbral | Veredicto |
|---|---|---|---|
| ROUGE-L (F1) | 0.171 | ≥0.35 | ❌ |
| BLEU (corpus) | 0.059 | ≥0.25 | ❌ |
| **Accuracy** | **0.72** (36/50) | ≥0.70 | ✅ |
| **Likert media** | **4.325** | ≥4.0 | ✅ |
| Cohen's κ inter-juez | 0.211 (Likert) / 0.239 (binario) | ≥0.60 | ❌ |

Desglose Likert por criterio (juez `llama3.1`, 1-5): exactitud **3.90** · fluidez **4.60** ·
sin alucinaciones **4.86** · pedagogía **3.94**.

---

## 4. Resultados — recuperación (embeddings seleccionado: mxbai)

| Métrica | SIN rerank (coseno) | **CON rerank (producción)** | Umbral | Veredicto |
|---|---|---|---|---|
| Recall@5 | 0.62 | **0.72** | ≥0.70 | ✅ |
| MRR@10 | 0.535 | **0.684** | ≥0.65 | ✅ |
| nDCG@10 | 0.568 | **0.686** | ≥0.55 | ✅ |

El **rerank cross-encoder** (config de producción) lleva las tres métricas sobre su umbral.
Relevancia binaria: chunk relevante si contiene ≥2 de los `expected_context_keywords`
(substring, case-insensitive); 50 queries, pool de 30 candidatos.

Por módulo (con rerank): M1 Recall@5 **1.00** · M4 **0.80** · M5 **0.90** · M2 **0.62** ·
M3 **0.45** (UI, el más débil). El agregado cumple.

> Nota: el índice pgvector está embebido con mxbai (1024 dim); `nomic-embed-text` (768 dim) no
> es comparable sin re-indexar y ya quedó descartado en el reporte-LLM original (Recall@5 0.35).
> La validación de recuperación es **consistente con OE2/RAGAS**: context_recall 0.812,
> context_precision 0.876 (instrumento ragas oficial).

---

## 5. Resultado — Spearman STS

| Métrica | Valor | Umbral | Veredicto |
|---|---|---|---|
| Spearman | 0.664 | ≥0.70 | ❌ |
| Pearson | 0.662 | — | — |

Dataset `stsb_multi_mt` (es), split test, **1379 pares**, gold humano 0-5.

---

## 6. Interpretación de los cuatro indicadores por debajo de umbral

### 6.1 ROUGE-L (0.171) y BLEU (0.059) — inadecuación del instrumento
Son métricas de **solapamiento n-gram** diseñadas para traducción automática y resumen, donde
la salida debe parecerse léxicamente a una referencia corta. El tutor RAG produce respuestas
**pedagógicas y extensas** (2-4 párrafos) frente a un `ground_truth` de 1-2 oraciones: la
precisión n-gram cae (numerador LCS pequeño / denominador respuesta larga) y arrastra el F1 y el
BLEU. **No miden corrección semántica**: una respuesta correcta pero parafraseada puntúa bajo.

La calidad real de generación está validada por **evidencia convergente**:
- Accuracy **0.72** (juez independiente, consistencia factual).
- Likert media **4.325** (juez independiente; sin alucinaciones 4.86).
- RAGAS [OE2]: faithfulness **0.706**, answer_relevancy **0.707**, answer_correctness **0.609**.

**Conclusión:** ROUGE-L y BLEU son el **instrumento equivocado** para un tutor generativo de
respuesta abierta; su bajo valor refleja desajuste de formato/longitud, no respuestas deficientes.

### 6.2 Cohen's κ (0.211 Likert / 0.239 binario) — fiabilidad inter-juez automatizada
Se midió con dos formulaciones, ambas bajas:
- **κ sobre Likert global** (cuadrático) = 0.211: las puntuaciones se concentran en 4-5 (poca
  varianza) → **paradoja de kappa** (marginales sesgadas deprimen κ aunque el acuerdo bruto sea alto).
- **κ sobre el veredicto binario `correcto`** = 0.239: acuerdo bruto 76 % (38/50), pero los dos
  jueces tienen **leniencia distinta** — llama3.1 marca correcto 72 %, llama3 92 % — lo que baja κ.

Ambas formulaciones coinciden en que el κ **inter-juez automatizado** es insuficiente, por la
calibración dispar entre jueces LLM, no por una evaluación poco fiable (el acuerdo bruto es alto).
El instrumento idóneo es la concordancia **multi-evaluador HUMANO** sobre una submuestra del golden
set, declarada como trabajo futuro (igual que en `reporte-LLM.docx`). No se escoge un 2º juez
distinto para inflar el acuerdo: sería *cherry-picking*.

### 6.3 Spearman STS (0.664) — fuera de dominio
`stsb_multi_mt` es similitud textual **simétrica de dominio general**; `mxbai-embed-large` está
optimizado para **recuperación asimétrica** (query↔documento), que es justamente la tarea del
sistema. La recuperación **de dominio** sí cumple (Recall@5 0.72, y RAGAS recall 0.812). El gap
en STS general es esperable para un embedding de recuperación evaluado en una tarea STS abierta.

---

## 7. Decisión (✅ aprobada por la asesora, 2026-05-29)

> La asesora **aprobó el encuadre** (`docs/oe1-encuadre-instrumentos-propuesta.md`): se adopta la
> clasificación de instrumentos primarios/secundarios. **OE1 queda validado** por sus instrumentos
> primarios (Accuracy, Likert + RAGAS para generación; Recall@5/MRR@10/nDCG@10 para recuperación);
> ROUGE-L, BLEU, STS general y κ automático = secundarias/diagnósticas; κ humano = trabajo futuro.

El patrón es **idéntico al de OE2/RAGAS**: varios umbrales fueron fijados como **aspiracionales**
sin calibrarse a la clase de tecnología (LLM 7B local sin fine-tuning; embedding de recuperación).
Caminos honestos, NO excluyentes:

1. **Declarar el instrumento apropiado por dimensión.** Generación: priorizar métricas
   **semánticas** (Accuracy, Likert, y las RAGAS de OE2), tratando ROUGE-L/BLEU como
   **secundarias/informativas** (análogo a `context_entity_recall` en OE2). Recuperación:
   las tres métricas canónicas (Recall@5/MRR@10/nDCG@10) **cumplen** con la config de producción.
2. **Cohen's κ:** reportar concordancia inter-juez LLM con la advertencia de la paradoja de
   kappa; planificar κ humano multi-evaluador como cierre (trabajo futuro ya declarado).
3. **Spearman STS:** documentar como métrica de dominio abierto, no central a la tarea de
   recuperación del tutor; la validación de recuperación de dominio (OE2) es la evidencia fuerte.
4. **Si se mantienen los umbrales aspiracionales**, fundamentar el gap de ROUGE/BLEU/STS con
   literatura (limitación de métricas n-gram para QA abierto; embeddings de recuperación vs STS)
   y dejarlo como limitación + trabajo futuro. **No insertar citas sin verificar.**

> **Protocolo de escalamiento (CLAUDE.md):** indicadores objetivo no alcanzados → detener y
> consultar a la asesora. **Resuelto 2026-05-29: la asesora aprobó el encuadre** (clasificación
> de instrumentos, no recalibración de umbrales).

---

## 8. Conclusiones

1. **Recuperación: CUMPLE** las tres métricas canónicas con la config de producción (rerank),
   consistente con OE2/RAGAS. El modelo `mxbai-embed-large` queda validado para la tarea.
2. **Generación semántica: CUMPLE** (Accuracy 0.72, Likert 4.325 con juez independiente). El LLM
   `qwen2.5:7b` queda validado en calidad y corrección factual.
3. **ROUGE-L, BLEU, STS general y κ** quedan por debajo de umbral por **inadecuación del
   instrumento a la tarea/tecnología**, no por deficiencia del sistema; requieren decisión de
   encuadre con la asesora (análoga a la recalibración de OE2).
4. **5/9 indicadores cumplen**; las dimensiones centrales del OE1 (calidad de generación y
   precisión de recuperación) están **validadas por instrumentos apropiados**. Bajo el **encuadre
   aprobado por la asesora (2026-05-29)** — instrumentos primarios como criterio, los cuatro
   restantes como secundarios/diagnósticos — **OE1 queda validado**; κ humano multi-evaluador
   queda como trabajo futuro.

---

## 9. Artefactos

- `backend/scripts/oe1_generation.py` · `oe1_retrieval.py` · `oe1_sts.py` (harness reproducible).
- `docs/oe1_generation_results.json` · `oe1_retrieval_results.json` · `oe1_sts_results.json`.
- `docs/oe1_generation_log.jsonl` (50 respuestas + 100 evaluaciones de juez).
- Golden set: `backend/tests/fixtures/golden_set.json` (50 ítems).
- Cross-referencia OE2: `docs/reporte-RAGAS.docx` (faithfulness 0.706, recall 0.812).

*Instrumentos reproducibles en el contenedor backend. El fundamento bibliográfico de las
decisiones de encuadre se integra en el documento de tesis.*

---

## 10. Adenda 2026-05-31 — Criterio OE1 finalizado (anteproyecto V.2.1)

La asesora confirmó la versión final del set de indicadores OE1 en el anteproyecto. El **criterio
de aprobación** lo forman los **instrumentos primarios**, todos cumplidos:

| Dimensión | Indicadores del criterio | Estado |
|---|---|---|
| Generación (qwen2.5) | Accuracy ≥0.70 (0.72) · Likert ≥4.0 (4.325) | ✅ 2/2 |
| Recuperación (mxbai) | nDCG@10 ≥0.55 (0.686) · Recall@5 ≥0.70 (0.72) · MRR@10 ≥0.65 (0.684) | ✅ 3/3 |

**ROUGE-L, BLEU, Cohen's κ automático y Spearman STS general se retiran del criterio formal** por
inadecuación del instrumento a la tarea/tecnología (justificación en §6), y se conservan en este
reporte **medidos como diagnóstico** — la medición de los 9 indicadores del §1 permanece intacta
como evidencia. Mismo precedente que `context_entity_recall` en OE2. **Resultado: 5/5 indicadores
primarios cumplen → OE1 validado.**
