# Reporte RAGAS v7 — Cross-check con la librería ragas OFICIAL

**Fecha:** 2026-05-29 · **OE:** OE2 · **Branch:** `feat/oe2-ragas-iter0`

## Propósito

Los umbrales oficiales (context_precision ≥0.70, context_recall ≥0.75, faithfulness ≥0.80, etc.) referencian las **definiciones canónicas de RAGAS**, no las aproximaciones custom de `run_ragas_eval.py`. Este reporte mide el MISMO pipeline (rerank cross-encoder on, juez `llama3.1:8b`, golden set 50q) con la **librería `ragas==0.2.6` oficial**, para comparar contra el umbral con el instrumento autoritativo.

Nota técnica: `ragas` es frágil con clientes no-OpenAI (CLAUDE.md). Se aplicó un parche de compatibilidad (`scripts/run_ragas_lib_eval.py`) que mueve `temperature` a `options` en `ollama.*.chat()`. Fiabilidad de la corrida: **~6 de 300 jobs** (50 preguntas × 6 métricas) fallaron por parser/timeout (~2%); ragas descarta esos por-muestra y promedia el resto.

## Resultado — instrumento OFICIAL vs custom (mismo pipeline)

| Métrica | Umbral | **ragas-lib (oficial)** | custom v6 | ¿Coinciden? |
|---|---|---|---|---|
| faithfulness | ≥0.80 | 0.706 ❌ | 0.727 ❌ | sí (ambos ~0.71, fallan) |
| answer_relevancy | ≥0.75 | 0.707 ❌ | 0.870 ✅ | **no** |
| context_precision | ≥0.70 | **0.876 ✅** | 0.589 ❌ | **no** |
| context_recall | ≥0.75 | **0.812 ✅** | 0.608 ❌ | **no** |
| context_entity_recall | ≥0.70 | 0.211 ❌ | 0.773 ✅ | **no** |
| answer_correctness | ≥0.70 | 0.609 ❌ | 0.742 ✅ | **no** |

**Bajo el instrumento oficial: cumplen 2/6 (context_precision, context_recall).**

## Interpretación

### 1. El retrieval SÍ cumple (hallazgo principal)
La `context_precision` oficial = **0.876** (vs custom 0.589) y `context_recall` oficial = **0.812** (vs custom 0.608). Ambas **superan el umbral**. La métrica custom (AP@k con juez "¿útil?") sub-medía sistemáticamente la precisión; nunca cruzó 0.70 en ninguna iteración, lo que era un **artefacto de la implementación**, no del pipeline.

**Consecuencia:** la recuperación del RAG (con rerank cross-encoder) está **validada** bajo el instrumento autoritativo. **La Iteración 2 (chunking semántico + re-index) ya no es necesaria para cerrar precision/recall.**

### 2. Los dos instrumentos discrepan en 5 de 6 métricas
Solo faithfulness coincide (ambos ~0.71). En las demás, custom y oficial difieren fuerte y hasta en el veredicto pass/fail. Conclusión metodológica fuerte: **las métricas RAGAS son sensibles a la implementación y al juez**; la tesis debe **declarar un único instrumento y justificarlo**, no combinar "lo mejor de cada uno" (sería cherry-picking).

### 3. La generación tiene un techo real (~0.71 faithfulness)
faithfulness 0.706 (oficial) ≈ 0.727 (custom): ambos instrumentos coinciden en que está **por debajo de 0.80**, con juez independiente honesto. Es el **techo de `qwen2.5:7b-q4` local** (modelo cerrado, sin fine-tuning, corpus privado). answer_correctness oficial 0.609 y answer_relevancy 0.707 también quedan bajo umbral con la lib.

### 4. Anomalía context_entity_recall oficial = 0.211
Contradice el custom (0.773). La `context_entity_recall` de ragas extrae entidades muy granulares del `reference` y exige presencia literal en los contextos; con `llama3.1` como extractor el parseo es inestable. **Requiere revisión** (posible artefacto de extracción/parse, no necesariamente recuperación deficiente).

## Implicación para OE2 (decisión de tesis)

- **Recuperación [parte de OE2]: CUMPLE** bajo el instrumento oficial (precision 0.876, recall 0.812). Resultado positivo y defendible.
- **Generación [parte de OE2]: por debajo** de los umbrales aspiracionales (faithfulness ~0.71, answer_correctness ~0.61). Los umbrales son **targets fijados por el tesista** (revisables con justificación). Caminos honestos:
  1. Justificar el gap por el constraint de modelo local 7B cuantizado (privacidad, sin fine-tuning) + benchmarks de literatura para LLM open-source self-hosted.
  2. Revisar los umbrales de generación a valores **empíricamente calibrados** para modelos locales (citando fuentes), no aspiracionales.
  3. Reportar faithfulness sobre el subconjunto apto (conceptual+application) según el diseño del golden set — aunque sigue ~0.73.
- **No combinar instrumentos.** Elegir la **librería ragas oficial** como instrumento (peer-reviewed, es lo que los umbrales referencian) y reportar las 6 con transparencia.

## Artefactos

- `backend/scripts/ragas_runs/20260529_1025_ragaslib.json` (medias oficiales)
- `backend/scripts/run_ragas_lib_eval.py` (script + parche compat ollama)
- Comparar con custom: `20260529_0640_v6_rerank.summary.json`

## Pendiente / siguiente decisión

1. ¿Adoptar ragas-lib como instrumento oficial de la tesis? (recomendado)
2. ¿Cómo enmarcar el gap de generación? (justificar vs recalibrar umbrales — decisión con asesora)
3. Investigar `context_entity_recall` oficial 0.211 (¿artefacto de parse?).
4. Opcional: κ inter-juez (llama3.1 vs gemma2) para blindar fiabilidad.
