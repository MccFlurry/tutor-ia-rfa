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

Dos cambios metodológicos vs v3/v4: (1) el juez ahora es **distinto del generador** (elimina sesgo de auto-preferencia); (2) instrumento endurecido tras review (parse JSON robusto, denominador de entities = nº de entidades extraídas, `answer_correctness` con conteo 0/0/0 → `None`, métricas de respuesta sólo cuando hay contexto). Los números de abajo son la corrida **endurecida** (`v5_hardened`), la autoritativa.

## Resultado global (50 preguntas) — corrida endurecida

| Métrica | Umbral oficial | v5 | Estado | none_rate |
|---|---|---|---|---|
| faithfulness | ≥0.80 | 0.699 | ❌ | 0.00 |
| answer_relevancy | ≥0.75 | 0.875 | ✅ | 0.00 |
| context_precision | ≥0.70 | 0.532 | ❌ | 0.00 |
| context_recall | ≥0.75 | 0.559 | ❌ | 0.00 |
| context_entities_recall | ≥0.70 | 0.703 | ✅ | 0.00 |
| answer_correctness | ≥0.70 | 0.762 | ✅ | 0.08 |

**Cumplen 3/6.** El none_rate 0.08 de `answer_correctness` (4/50) es honesto: el fix convierte clasificaciones 0/0/0 del juez en no-medición en vez de un falso score bajo.

## Efecto del endurecimiento del instrumento (v5_baseline → v5_hardened)

| Métrica | v5_baseline (buggy) | v5_hardened | Causa del Δ |
|---|---|---|---|
| faithfulness | 0.678 | 0.699 | recuperación de parse JSON (menos claims perdidos) |
| context_entities_recall | 0.690 | **0.703** | denominador = nº entidades; **cruza umbral** |
| answer_correctness | 0.720 | 0.762 | parse robusto + 0/0/0→None (quita falsos bajos) |
| answer_relevancy | 0.858 | 0.875 | parse robusto |
| context_precision / recall | 0.532 / 0.559 | 0.532 / 0.559 | sin cambio (lógica no tocada) |

## Efecto del juez independiente (v4 juez=qwen2.5 → v5 juez=llama3.1:8b)

| Métrica | v4 (auto-juez) | v5 (juez indep.) | Lectura |
|---|---|---|---|
| faithfulness | 0.774 | 0.699 | el auto-juez **inflaba** fidelidad |
| context_precision | 0.263 | 0.532 | el auto-juez era **demasiado estricto** (~2×) |
| context_recall | 0.650 | 0.559 | comparable/algo menor |
| answer_relevancy | 0.866 | 0.875 | estable |

## Breakdown por tipo (endurecido)

| Tipo | n | faithfulness | ctx_precision | ctx_recall | entities_recall | answer_correctness |
|---|---|---|---|---|---|---|
| conceptual | 25 | 0.679 | 0.538 | 0.576 | 0.637 | 0.784 |
| application | 11 | 0.776 | 0.539 | 0.586 | 0.676 | 0.712 |
| code | 14 | 0.673 | 0.516 | 0.507 | 0.841 | 0.760 |

> Faithfulness sobre subconjunto apto (conceptual+application, 36 q) = (0.679·25 + 0.776·11)/36 = **0.709** — sigue < 0.80 con juez honesto. Gap real.

## Breakdown por módulo (endurecido)

| Módulo | n | faithfulness | ctx_precision | ctx_recall | entities_recall | answer_correctness |
|---|---|---|---|---|---|---|
| M1 | 6 | 0.784 | 0.553 | 0.534 | 0.672 | 0.644 |
| M2 | 13 | 0.652 | 0.532 | 0.537 | 0.735 | 0.762 |
| M3 | 11 | 0.682 | 0.575 | 0.638 | 0.592 | 0.789 |
| M4 | 10 | 0.683 | 0.498 | 0.488 | 0.768 | 0.819 |
| M5 | 10 | 0.742 | 0.507 | 0.587 | 0.735 | 0.752 |

## Métricas < umbral → input al Decision Gate (Iteración 1)

1. **context_precision 0.532** (faltan 0.168): uniforme ~0.50-0.57 en todos los cortes → sistémico de `top_k=7` demasiado ancho. M4 (0.498) el más bajo. **Palanca principal: retrieve-then-rerank + bajar top_k final a 4-5.**
2. **context_recall 0.559** (faltan 0.191): M4 (0.488) y `code` (0.507) más débiles. **Palanca: fetch ancho antes del rerank; chunking semántico (iter 2) si no basta.**
3. **faithfulness 0.699** (faltan 0.101): aun en subconjunto apto = 0.709. `code` (0.673) y M2 (0.652) arrastran. Palancas: contexto más limpio (rerank → menos claims sin respaldo), prompt de grounding más estricto. **Riesgo: el más incierto de cerrar a 0.80 → vigilar protocolo de 3 iteraciones.**

**Ya cumplen (3):** answer_relevancy 0.875, context_entities_recall 0.703, answer_correctness 0.762.

## Artefactos

- `backend/scripts/ragas_runs/20260529_0539_v5_hardened.{csv,summary.json}` (autoritativo, 50 q)
- `backend/scripts/ragas_runs/20260529_0506_v5_baseline.{csv,summary.json}` (pre-endurecimiento, referencia del Δ)

## Nota de ejecución

Juez inyectado vía `docker compose exec -e RAGAS_JUDGE_MODEL=llama3.1:8b` (sin editar `.env` ni reiniciar; `pydantic-settings` lee el entorno del proceso). κ omitido por diseño (juez único).
