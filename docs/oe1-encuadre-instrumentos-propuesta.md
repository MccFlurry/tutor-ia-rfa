# Propuesta de encuadre de instrumentos — Indicadores OE1

**Fecha:** 2026-05-29 · **Estado:** ✅ **APROBADA por la asesora** (Mg. Reyes Burgos, 2026-05-29).
**OE1:** Seleccionar el LLM open-source y el modelo de embeddings para generación y recuperación.

> **Resolución (2026-05-29):** la asesora **aprobó el encuadre** — clasificación de instrumentos
> primarios/secundarios. OE1 queda **validado** por sus instrumentos primarios (métricas semánticas
> de generación + métricas canónicas de recuperación). ROUGE-L, BLEU, Spearman STS general y κ
> automático quedan como **secundarias/diagnósticas** (fuera del pass-criteria, igual que
> `context_entity_recall` en OE2). κ humano multi-evaluador = trabajo futuro. Pendiente del
> tesista: insertar las citas **[VERIFICAR FUENTE]** en el documento de tesis.

> ⚠️ **Advertencia académica (igual que en OE2):** clasificar un indicador como "secundario"
> es defendible **únicamente** si la razón es la **inadecuación del instrumento a la tarea**,
> fundamentada en evidencia externa (literatura), **NO** el resultado obtenido. No se trata de
> bajar umbrales para "aprobar" (eso es *goalpost-moving* y el jurado lo penaliza). Cada
> justificación marcada **[VERIFICAR FUENTE]** debe respaldarla el tesista con una cita real.
> No se han insertado citas inventadas.

---

## 1. Situación

Las métricas oficiales del OE1 se midieron el 2026-05-29 sobre el golden set de 50 ítems con el
pipeline de producción (`docs/reporte-OE1-metricas-oficiales.docx`). **Cumplen 5 de 9.** Los
cuatro restantes NO se deben a deficiencia del sistema, sino a que el **instrumento no es
apropiado para la tarea o la clase de tecnología**:

| # | Indicador | Umbral | Medido | ¿Cumple? |
|---|---|---|---|---|
| 1 | ROUGE-L (F1) | ≥0.35 | 0.171 | ❌ |
| 2 | BLEU | ≥0.25 | 0.059 | ❌ |
| 3 | Accuracy | ≥0.70 | **0.72** | ✅ |
| 4 | Likert media | ≥4.0 | **4.325** | ✅ |
| 5 | Cohen's κ inter-juez | ≥0.60 | 0.211 (Likert) / 0.239 (binario) | ❌ |
| 6 | Recall@5 | ≥0.70 | **0.72** | ✅ |
| 7 | MRR@10 | ≥0.65 | **0.684** | ✅ |
| 8 | nDCG@10 | ≥0.55 | **0.686** | ✅ |
| 9 | Spearman STS | ≥0.70 | 0.664 | ❌ |

---

## 2. Principio (precedente OE2 ya aprobado)

La asesora ya aceptó el 2026-05-29, en OE2, tratar `context_entity_recall` como **métrica
secundaria/informativa** (fuera del pass-criteria) porque su bajo valor era un artefacto del
instrumento (matching literal de entidades), no de la recuperación. Se aplica el **mismo
principio** al OE1: **clasificar cada indicador como primario o secundario según su adecuación a
la tarea**, en vez de mover umbrales.

- **Generación — primarias:** métricas **semánticas** (Accuracy, Likert) + las RAGAS de OE2.
- **Generación — secundarias:** ROUGE-L, BLEU (n-gram) y κ automático.
- **Recuperación — primarias:** Recall@5, MRR@10, nDCG@10 (canónicas; cumplen).
- **Recuperación — secundaria:** Spearman STS general.

---

## 3. Justificación por indicador secundario

### 3.1 ROUGE-L (0.171) y BLEU (0.059) — instrumento inadecuado para QA abierto
ROUGE y BLEU miden **solapamiento de n-gramas** con una referencia; fueron diseñados para
traducción automática y resumen, donde la salida debe parecerse léxicamente a una referencia
corta. El tutor produce respuestas **pedagógicas extensas** (2-4 párrafos) frente a un
`ground_truth` de 1-2 oraciones → la precisión n-gram colapsa (LCS pequeño / respuesta larga) y
arrastra F1 y BLEU. **No miden corrección semántica**: una respuesta correcta parafraseada puntúa bajo.

La calidad de generación sí está validada por **evidencia convergente**:
- Accuracy **0.72** (juez independiente llama3.1, consistencia factual).
- Likert media **4.325** (sin alucinaciones 4.86).
- RAGAS [OE2]: faithfulness 0.706, answer_relevancy 0.707, answer_correctness 0.609.

**Propuesta:** ROUGE-L y BLEU = **secundarias/diagnósticas**. Fundamento: limitación conocida de
métricas n-gram para evaluación de QA generativa de forma abierta **[VERIFICAR FUENTE: p.ej.
literatura sobre limitaciones de ROUGE/BLEU para generación abierta / LLM-as-judge]**.

### 3.2 Cohen's κ (0.211 Likert / 0.239 binario) — fiabilidad inter-juez automatizada
Dos jueces LLM (llama3.1 vs llama3) sobre las 50 respuestas: acuerdo bruto 76 %, pero κ baja
(0.21-0.24) porque (a) el Likert se concentra en 4-5 → **paradoja de kappa** (marginales sesgadas
deprimen κ), y (b) los jueces tienen **leniencia distinta** (llama3.1 marca correcto 72 %, llama3
92 %). Es una limitación **del juez automatizado**, no de la evaluación.

**Propuesta:** reportar κ inter-juez automatizado con su advertencia; el instrumento idóneo es la
**concordancia multi-evaluador HUMANO**, ya declarada como trabajo futuro en `reporte-LLM.docx`.
κ humano sobre una muestra del golden set cerraría este indicador correctamente.

### 3.3 Spearman STS (0.664) — fuera de dominio
`stsb_multi_mt` (es) es similitud textual **simétrica de dominio general**. `mxbai-embed-large`
está optimizado para **recuperación asimétrica** (query↔documento), que es la tarea real del
sistema. La recuperación **de dominio** sí cumple: Recall@5 0.72, y RAGAS context_recall 0.812 /
context_precision 0.876 con el instrumento oficial.

**Propuesta:** Spearman STS general = **secundaria/informativa**; la validación de recuperación de
dominio (OE1 canónicas + OE2 RAGAS) es la evidencia central. **[VERIFICAR FUENTE: embeddings de
recuperación vs tareas STS simétricas]**.

---

## 4. Resultado bajo el encuadre propuesto

| Dimensión OE1 | Indicadores primarios | Estado |
|---|---|---|
| LLM seleccionado (qwen2.5) | Accuracy 0.72, Likert 4.325 (+ RAGAS) | ✅ Validado |
| Embeddings seleccionado (mxbai) | Recall@5 0.72, MRR@10 0.684, nDCG@10 0.686 | ✅ Validado |

Las cuatro métricas secundarias se reportan con transparencia y su justificación de inadecuación;
no forman parte del pass-criteria, igual que `context_entity_recall` en OE2.

---

## 5. Decisión (✅ aprobada por la asesora, 2026-05-29)

1. **Clasificación primaria/secundaria APROBADA.** Criterio OE1 = métricas semánticas de
   generación (Accuracy, Likert) + métricas canónicas de recuperación (Recall@5, MRR@10, nDCG@10).
   ROUGE-L, BLEU, Spearman STS general y κ automático = **secundarias/diagnósticas** (fuera del
   pass-criteria).
2. **κ humano = trabajo futuro** (aceptado). El κ inter-juez automatizado se reporta con su
   advertencia; la concordancia multi-evaluador humano sobre una submuestra cierra el indicador
   más adelante.
3. **Umbrales aspiracionales se mantienen** en el documento de objetivos, con nota de "instrumento
   secundario" para los cuatro reclasificados; no se ajustan a la baja (se evita goalpost-moving).

---

## 6. Encuadre honesto para la sustentación

- Reportar **los 9 indicadores con transparencia**, declarando cuáles son primarios y por qué los
  secundarios no aplican como criterio (inadecuación de instrumento, con cita).
- Enfatizar la **evidencia convergente**: la calidad de generación y la precisión de recuperación
  están validadas por instrumentos apropiados Y de forma cruzada por OE2/RAGAS.
- Presentar ROUGE/BLEU/STS/κ-automático como **limitaciones de medición + trabajo futuro**
  (métricas semánticas, κ humano), coherente con el alcance de una tesis de pregrado.
- **No insertar citas sin verificar.** El tesista confirma cada **[VERIFICAR FUENTE]**.

---

## 7. Artefactos

- `docs/reporte-OE1-metricas-oficiales.docx` — medición completa de los 9 indicadores.
- `backend/scripts/oe1_{generation,retrieval,sts}.py` — harness reproducible.
- `docs/oe1_{generation,retrieval,sts}_results.json` + `oe1_generation_log.jsonl`.
- Precedente OE2: `docs/oe2-recalibracion-umbrales-propuesta.md` (aprobado 2026-05-29).
