# Reporte RAGAS v6 — Iteración 1: retrieve-then-rerank con cross-encoder

**Fecha:** 2026-05-29 · **OE:** OE2 · **Iteración:** 1 · **Branch:** `feat/oe2-ragas-iter0`

## Configuración

| Parámetro | Valor |
|---|---|
| Generador | `qwen2.5:7b-instruct-q4_K_M` |
| Juez (independiente) | `llama3.1:8b` |
| Embeddings | `mxbai-embed-large` |
| **Re-ranking** | **`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`** |
| fetch_k / fetch_threshold | 30 / 0.50 |
| top_k final | 7 |
| Chunking | RecursiveCharacterTextSplitter 500/50 (sin cambios) |
| Golden set | 50 preguntas (M1-M5) |

Pipeline: recuperar 30 candidatos por coseno (umbral laxo 0.50) → reordenar con cross-encoder multilingüe → devolver top 7. **Latencia rerank medida: 72 ms/query** (30 pares, CPU) — despreciable frente al presupuesto OE3 (e2e ≤8s).

## Resultado global — v5 (sin rerank) → v6 (con rerank)

| Métrica | Umbral | v5_hardened | v6_rerank | Δ | Estado v6 |
|---|---|---|---|---|---|
| faithfulness | ≥0.80 | 0.699 | 0.727 | +0.028 | ❌ |
| answer_relevancy | ≥0.75 | 0.875 | 0.870 | −0.005 | ✅ |
| context_precision | ≥0.70 | 0.532 | 0.589 | +0.057 | ❌ |
| context_recall | ≥0.75 | 0.559 | 0.608 | +0.049 | ❌ |
| context_entities_recall | ≥0.70 | 0.703 | 0.773 | +0.070 | ✅ |
| answer_correctness | ≥0.70 | 0.762 | 0.742 | −0.020 | ✅ |

**Cumplen 3/6** (igual que v5, pero `context_entities_recall` ahora con margen amplio). El re-ranking movió **las cuatro métricas de recuperación/fidelidad en la dirección correcta**, pero no cerró tres:
- context_precision 0.589 (faltan 0.111)
- context_recall 0.608 (faltan 0.142) — la más lejana
- faithfulness 0.727 (faltan 0.073)

none_rate v6: faithfulness 0.00, context_recall 0.02, answer_correctness 0.06 — honesto, bajo.

## Breakdown por tipo (v6)

| Tipo | n | faithfulness | ctx_precision | ctx_recall | entities_recall |
|---|---|---|---|---|---|
| conceptual | 25 | 0.723 | 0.603 | 0.613 | 0.817 |
| application | 11 | 0.751 | 0.555 | 0.637 | 0.691 |
| code | 14 | 0.716 | 0.588 | 0.573 | 0.759 |

(Breakdowns completos por módulo/dificultad en `scripts/ragas_runs/20260529_0640_v6_rerank.summary.json`.)

## Análisis

El cross-encoder mejora la precisión del top-k (reordena candidatos relevantes hacia arriba) y, al ampliar el pool inicial a 30, también sube recall. Pero persiste la **tensión precision↔recall** estructural: con `top_k=7` sobre chunks de 500 caracteres, el contexto sigue fragmentado:
- subir top_k mejoraría recall pero bajaría precision;
- bajar top_k mejoraría precision pero hundiría recall (ya en 0.608, la más débil).

La palanca que mueve **ambas a la vez** es **chunking semántico** (chunks coherentes y auto-contenidos → cada uno aporta información completa → más recall sin perder precision, y mejor grounding → faithfulness). Es la Iteración 2.

**Riesgo faithfulness:** con juez independiente honesto, faithfulness 0.727 (gap 0.073 a 0.80). Las respuestas de `code` generan sentencias nuevas no literales en el corpus → techo natural. Aun en subconjunto apto (conceptual+application) ronda ~0.73. Cerrar a 0.80 con `qwen2.5:7b` (modelo cerrado) es incierto.

## Estado del protocolo de iteración

- v5_hardened = baseline (iter 0)
- **v6_rerank = iteración 1** (esta)
- Iteración 2 candidata = chunking semántico + re-index
- Protocolo CLAUDE.md: si una métrica sigue < umbral tras **3 iteraciones** → detener y consultar al usuario. Tras iter 2 se habrá agotado el margen para precision/recall/faithfulness.

## Artefactos

- `backend/scripts/ragas_runs/20260529_0640_v6_rerank.{csv,summary.json}`
- Rerank: `app/services/rerank_service.py`, config `RAG_RERANK=cross_encoder`, latencia 72 ms/query.
