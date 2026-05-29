# Reporte RAGAS v5 — re-baseline bajo umbrales oficiales + juez independiente

**Fecha:** 2026-05-29 · **OE:** OE2 · **Iteración:** 0 (instrumentación) · **Branch:** `feat/oe2-ragas-iter0`

## Configuración

| Parámetro | Valor |
|---|---|
| Generador | `qwen2.5:7b-instruct-q4_K_M` |
| **Juez (independiente)** | **`llama3.1:8b`** |
| Juez B (κ) | — (no configurado) |
| Embeddings | `mxbai-embed-large` (1024 dim) |
| Chunking | RecursiveCharacterTextSplitter 500/50 |
| Retrieval | coseno, threshold 0.65, top_k 7 |
| Golden set | 50 preguntas (M1-M5), v1.2 |

Cambio metodológico clave vs v3/v4: el juez ahora es **distinto del generador** (elimina sesgo de auto-preferencia). Esto reconfigura los números — son la **medición honesta**.

## Resultado global (50 preguntas)

| Métrica | Umbral oficial | v5 | Estado | none_rate |
|---|---|---|---|---|
| faithfulness | ≥0.80 | 0.678 | ❌ | 0.00 |
| answer_relevancy | ≥0.75 | 0.858 | ✅ | 0.00 |
| context_precision | ≥0.70 | 0.532 | ❌ | 0.00 |
| context_recall | ≥0.75 | 0.559 | ❌ | 0.00 |
| context_entities_recall | ≥0.70 | 0.690 | ❌ (a 0.01) | 0.00 |
| answer_correctness | ≥0.70 | 0.720 | ✅ | 0.04 |

**Cumplen 2/6.** none_rate ≈0 (solo answer_correctness 0.04 → 2/50 sin valor por JSON inválido del juez; tolerable).

## Comparación con mediciones previas (efecto del juez independiente)

| Métrica | v3 (juez=qwen2.5) | v4 (juez=qwen2.5) | **v5 (juez=llama3.1:8b)** | Lectura |
|---|---|---|---|---|
| faithfulness | 0.768 | 0.774 | **0.678** | El auto-juez **inflaba** fidelidad; honesto es menor |
| context_precision | 0.290 | 0.263 | **0.532** | El auto-juez era **demasiado estricto**; medición real ~2× |
| context_recall | 0.619 | 0.650 | **0.559** | Comparable |
| answer_relevancy | 0.856 | 0.866 | **0.858** | Estable (no depende del juez) |

Conclusión metodológica: cambiar el juez **sube precision** (0.26→0.53) y **baja faithfulness** (0.77→0.68). Ambos efectos son esperables al quitar el sesgo generador=juez, y dejan un punto de partida defendible.

## Breakdown por tipo

| Tipo | n | faithfulness | ctx_precision | ctx_recall | entities_recall | answer_correctness |
|---|---|---|---|---|---|---|
| conceptual | 25 | 0.673 | 0.538 | 0.576 | 0.641 | 0.759 |
| application | 11 | 0.733 | 0.539 | 0.586 | 0.671 | 0.694 |
| code | 14 | 0.643 | 0.516 | 0.507 | 0.793 | 0.671 |

> Faithfulness sobre subconjunto apto (conceptual+application, 36 q) = (0.673·25 + 0.733·11)/36 = **0.691** — sigue < 0.80 con el juez honesto. El gap de faithfulness es real, no solo arrastrado por `code`.

## Breakdown por dificultad

| Dificultad | n | faithfulness | ctx_precision | ctx_recall | entities_recall | answer_correctness |
|---|---|---|---|---|---|---|
| easy | 17 | 0.735 | 0.535 | 0.625 | 0.787 | 0.653 |
| medium | 27 | 0.668 | 0.532 | 0.519 | 0.667 | 0.746 |
| hard | 6 | 0.560 | 0.523 | 0.552 | 0.520 | 0.814 |

## Breakdown por módulo

| Módulo | n | faithfulness | ctx_precision | ctx_recall | entities_recall | answer_correctness |
|---|---|---|---|---|---|---|
| M1 | 6 | 0.767 | 0.553 | 0.534 | 0.672 | 0.651 |
| M2 | 13 | 0.656 | 0.532 | 0.537 | 0.742 | 0.785 |
| M3 | 11 | 0.615 | 0.575 | 0.638 | 0.587 | 0.645 |
| M4 | 10 | 0.621 | 0.498 | 0.488 | 0.681 | 0.765 |
| M5 | 10 | 0.779 | 0.507 | 0.587 | 0.755 | 0.730 |

## Métricas < umbral → input al Decision Gate (Iteración 1)

1. **context_precision 0.532** (faltan 0.168): uniforme ~0.50-0.57 en todos los cortes → sistémico de `top_k=7` demasiado ancho. **Palanca: retrieve-then-rerank + bajar top_k final.**
2. **context_recall 0.559** (faltan 0.191): M4 (0.488) y `code` (0.507) más débiles. **Palanca: fetch ancho antes del rerank; chunking semántico (iter 2) si no basta.**
3. **context_entities_recall 0.690** (falta 0.010): debería cruzar con mejor recall; M3 (0.587) y `hard` (0.52) lo bajan.
4. **faithfulness 0.678** (faltan 0.122): **el más difícil.** Aun en subconjunto apto = 0.691. `code` (0.643) y `hard` (0.56) arrastran. Palancas: contexto más limpio (rerank), prompt de grounding más estricto, temperatura. **Riesgo: puede no cerrar a 0.80 → vigilar protocolo de 3 iteraciones.**

## Artefactos

- `backend/scripts/ragas_runs/20260529_0506_v5_baseline.csv` (per-row, 50 q)
- `backend/scripts/ragas_runs/20260529_0506_v5_baseline.summary.json` (agregados + breakdowns)

## Nota de ejecución

El juez se inyectó vía `docker compose exec -e RAGAS_JUDGE_MODEL=llama3.1:8b` (sin editar `.env` ni reiniciar el contenedor; `pydantic-settings` lo lee del entorno del proceso). κ omitido por diseño (juez único).
