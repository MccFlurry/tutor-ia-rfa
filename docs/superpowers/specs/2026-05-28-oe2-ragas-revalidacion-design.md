# Diseño — OE2 RAGAS re-validación bajo umbrales oficiales (staged)

**Fecha:** 2026-05-28 · **OE:** OE2 · **Sprint:** re-validación (origen S4, cierre hacia S8) · **Autor:** Roger Zavaleta (tesista) + Claude Code

## 1. Contexto y problema

El pipeline RAG fue validado en RAGAS v4 (2026-05-22, 50 preguntas M1-M5, corpus 3381 chunks) contra umbrales **antiguos y laxos** (faithfulness ≥0.75, answer_relevancy ≥0.70; precision/recall solo informativas). El CLAUDE.md v3.2 fijó los umbrales **oficiales** del mapeo V.2.1, más estrictos. Bajo esos umbrales, v4 NO cumple:

| Métrica oficial | Umbral | v4 medido | Estado |
|---|---|---|---|
| faithfulness | ≥0.80 | 0.774 | ❌ |
| answer_relevancy | ≥0.75 | 0.866 | ✅ |
| context_precision | ≥0.70 | 0.263 | ❌❌ |
| context_recall | ≥0.75 | 0.650 | ❌ |
| context_entities_recall | ≥0.70 | no medida | ⚠️ |
| answer_correctness | ≥0.70 | no medida | ⚠️ |

**Diagnóstico de la causa raíz:** `backend/scripts/run_ragas_eval.py:190` (`metric_context_precision`) calcula AP@k con juez LLM sobre `top_k=7`. Cada pregunta tiene ~1-2 chunks de soporte real; los 5-6 chunks restantes son tangenciales y el juez los marca no-útiles → precision colapsa. Existe una **tensión precision↔recall**: subir `top_k` / bajar `threshold` ayuda recall pero hunde precision; lo inverso también. Cerrar 0.263 → 0.70 solo tuneando parámetros es improbable.

Limitación metodológica adicional: el juez LLM actual es `qwen2.5`, **el mismo modelo que genera** las respuestas (sesgo de auto-preferencia).

## 2. Objetivo y criterios de éxito

Cumplir los **6 umbrales oficiales** sobre el golden set de 50 preguntas (M1-M5):
faithfulness ≥0.80 · answer_relevancy ≥0.75 · context_precision ≥0.70 · context_recall ≥0.75 · context_entities_recall ≥0.70 · answer_correctness ≥0.70.

Con: juez LLM **independiente** del generador, y acuerdo **Cohen's κ ≥0.60** entre dos jueces (cubierto con dos jueces-LLM de forma automatizada y defendible).

## 3. Restricciones (de CLAUDE.md)

- 100% local vía Ollama; **nunca APIs pagas**. No usar la librería `ragas` (frágil con LLM no-OpenAI) — métricas custom.
- Modelo generador **cerrado**: `qwen2.5:7b-instruct-q4_K_M` + `mxbai-embed-large`. No cambiar el generador.
- Protocolo de escalamiento: si una métrica sigue < umbral tras **3 iteraciones** → detener y consultar al usuario.
- Pipeline de retrieval **modificable** (decisión del usuario 2026-05-28).
- Verificar tags oficiales de modelos Ollama / HuggingFace antes de citar versiones o hacer pull.

## 4. Decisiones tomadas (2026-05-28)

1. **Enfoque A — staged** (incremental, medible por iteración).
2. **Juez independiente**: modelo local distinto del generador (candidatos `llama3.1:8b` o `gemma2:9b` — verificar tag). Doble juez para κ.
3. **Reranker**: se elige en iter 1, con datos del re-baseline (no comprometer dependencia a ciegas).

## 5. Arquitectura

### 5.1 Métricas (`backend/scripts/ragas_metrics.py` — nuevo módulo)

Extraer las funciones de métrica desde `run_ragas_eval.py` a un módulo aislado y testeable. Cada métrica es una función async con firma clara `(judge, ...) -> float | None`. Se conservan las 4 actuales (faithfulness, answer_relevancy, context_precision, context_recall) y se añaden 2:

- **`metric_context_entities_recall(judge, ground_truth, contexts) -> float`**: el juez extrae las entidades clave del `ground_truth` (términos técnicos, nombres de API, clases, conceptos); score = |entidades presentes en contexts| / |entidades totales|. La presencia se decide por coincidencia normalizada (case/acentos) con respaldo de juicio LLM para sinónimos.
- **`metric_answer_correctness(judge, embedder, answer, ground_truth) -> float`**: fórmula estilo RAGAS = `0.75 · F1_factual + 0.25 · coseno(answer, ground_truth)`. F1 factual: el juez clasifica claims en TP (en answer y ground_truth), FP (en answer, no en ground_truth), FN (en ground_truth, no en answer) → F1 = TP / (TP + 0.5·(FP+FN)).

**Auditoría de `context_precision`**: revisar que la normalización AP@k corresponda a la definición oficial "context precision with reference". Si está mal normalizada, corregir. Iter 0 confirmará si 0.263 es un valor real o un artefacto de medición.

Umbrales en `run_ragas_eval.py` → los **6 oficiales**; `pass` por métrica; `summary.json` reporta las 6 + breakdowns por module/type/difficulty + κ.

### 5.2 Juez independiente + κ

- Config nueva `RAGAS_JUDGE_MODEL` (env). `make_judge()` la usa; el generador y `query_rag` siguen con `qwen2.5`.
- `make_judge_b()` opcional con un segundo modelo local. Para los verdicts binarios (faithfulness supported, recall attributable, precision useful), computar **Cohen's κ** entre juez A y B → satisface "2 jueces, κ ≥0.60". κ se reporta en el summary.

### 5.3 Retrieval con reranking (iter 1, tras re-baseline)

Extender `app/services/rag_service.py::_semantic_search` (firma actual `(query_vec, db, top_k=None, threshold=None)`):

- Añadir `fetch_k` (recuperación ancha, ej. 25-30, threshold bajo/nulo) → reordenar candidatos → devolver `top_k` final (ej. 4-5).
- Config: `RAG_FETCH_K`, `RAG_RERANK` (`off|mmr|cross_encoder|llm`), `RAG_TOP_K`.
- Gated por config: con `RAG_RERANK=off` el comportamiento es el actual (no rompe producción ni tests existentes). El reranker concreto se implementa **uno solo**, el elegido en iter 1.

### 5.4 Chunking semántico (iter 2, condicional)

Solo si tras iter 1 recall o faithfulness siguen cortos: añadir splitter semántico (15% overlap) en `app/utils/chunking.py`, usado por `ingest_service`, + script de re-index que re-embebe el corpus. Cierra el objetivo v4.0 pendiente.

## 6. Flujo de datos (evaluación)

```
golden_set.json (50q)
  └─ por pregunta:
       run_rag(question) → (answer, contexts)         # pipeline real (con/sin rerank según config)
       ├─ faithfulness(juezA, answer, contexts)
       ├─ answer_relevancy(gen, embedder, q, answer)
       ├─ context_precision(juezA, q, ground_truth, contexts)
       ├─ context_recall(juezA, ground_truth, contexts)
       ├─ context_entities_recall(juezA, ground_truth, contexts)   # nueva
       ├─ answer_correctness(juezA, embedder, answer, ground_truth) # nueva
       └─ [juezB sobre verdicts binarios → κ]
  → CSV per-row + summary.json (global + by_module/type/difficulty + κ + pass por umbral)
```

## 7. Manejo de errores

- LLM devuelve JSON inválido → métrica `None`, excluida del promedio (comportamiento actual). **Nuevo:** rastrear None-rate por métrica; si es alta, marcar la métrica como poco fiable en el summary.
- Modelo juez no descargado en Ollama → fallar rápido con mensaje claro (no degradar en silencio).
- Dependencia de reranker ausente (ej. sentence-transformers) → fallback a `RAG_RERANK=off` + warning visible.

## 8. Testing

- **Unit por métrica** (`backend/tests/unit/test_ragas_metrics.py`): fixtures sintéticos con juez **mockeado** (sin LLM vivo). Casos: todo soportado → 1.0; nada soportado → 0.0; parcial → valor esperado. TDD obligatorio para las 2 métricas nuevas.
- **Unit de κ**: matriz de acuerdo conocida → κ esperado.
- **Integration** = la corrida real del eval (manual, requiere GPU/Ollama). No entra en la suite automática.

## 9. Protocolo de iteración

- **Iter 0:** métricas fieles + 2 nuevas + juez independiente + κ + umbrales oficiales. Re-baseline sobre las 50q. Objetivo: conocer el punto de partida REAL.
- **Iter 1:** retrieve-then-rerank (reranker elegido con datos de iter 0). Medir.
- **Iter 2 (condicional):** chunking semántico + re-index, si recall/faithfulness siguen cortos.
- Cada iter: correr 50q, guardar en `backend/scripts/ragas_runs/`, comparar. ≤3 iters por métrica; si una métrica < umbral tras 3 → **detener y consultar al usuario**.

## 10. Entregables

- `backend/scripts/ragas_metrics.py` (extraído + 2 métricas nuevas + κ).
- `run_ragas_eval.py` (6 métricas, juez configurable, doble juez κ, umbrales oficiales).
- `backend/tests/unit/test_ragas_metrics.py`.
- Extensión de `_semantic_search` + config en `.env.example` (iter 1).
- `docs/reporte-RAGAS.docx` — sección "Iteración v5" con resultados finales.
- Actualizar CLAUDE.md (números v5, estado OE2).

## 11. YAGNI / fuera de alcance

- Sin APIs pagas, sin librería `ragas`.
- Un solo reranker implementado (el de iter 1), no los tres.
- Chunking semántico solo si iter 1 no basta.
- Anotación humana de jueces: el usuario confirmó que los jueces aprueban; se genera material/κ con jueces-LLM. No se bloquea por disponibilidad humana.
- OE3 deploy real (VM/Firebase) fuera de alcance: usuario sin GCP aún.
