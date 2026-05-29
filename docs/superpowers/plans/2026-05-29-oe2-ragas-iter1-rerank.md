# OE2 RAGAS — Iteración 1 (retrieve-then-rerank con cross-encoder) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Subir context_precision (0.532→≥0.70), context_recall (0.559→≥0.75) y, por arrastre, faithfulness (0.699→≥0.80) añadiendo un re-ranking cross-encoder multilingüe al retrieval: recuperar ancho por coseno → reordenar por relevancia query↔chunk → cortar a top_k preciso.

**Architecture:** El rerank se inserta DENTRO de `_semantic_search` (no solo en `query_rag`) porque el evaluador RAGAS llama `_semantic_search` directamente para obtener los `contexts` que mide. Config-gated (`RAG_RERANK=off|cross_encoder`): con `off` el comportamiento es idéntico al actual (no rompe prod ni tests). Lazy-load del modelo; fallback a orden por coseno si el modelo no carga.

**Tech Stack:** Python 3.12, sentence-transformers (CrossEncoder, **nueva dependencia**, +torch), pytest. Cross-encoder corre en CPU dentro del contenedor backend (Ollama sigue nativo/GPU aparte).

**Baseline (v5_hardened, juez llama3.1:8b):** faithfulness 0.699 ❌ · answer_relevancy 0.875 ✅ · context_precision 0.532 ❌ · context_recall 0.559 ❌ · context_entities_recall 0.703 ✅ · answer_correctness 0.762 ✅.

**⚠️ Impacto OE3:** el rerank entra al path de producción → añade latencia/query (CPU). Medir el overhead. Si rompe el presupuesto OE3 (TTFT P95 ≤2.5s, e2e ≤8s), evaluar bajar `RAG_FETCH_K` o modelo más liviano.

**⚠️ Verificar antes de usar:** confirmar el tag del cross-encoder en HuggingFace (`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`, multilingüe incl. español, ~120MB). Alternativa más fuerte/pesada: `BAAI/bge-reranker-v2-m3`.

---

## Estructura de archivos

- **Modify** `backend/requirements.txt` — añadir `sentence-transformers`.
- **Modify** `backend/app/config.py` — `RAG_RERANK`, `RAG_FETCH_K`, `RAG_FETCH_THRESHOLD`, `RERANK_MODEL`.
- **Create** `backend/app/services/rerank_service.py` — lazy CrossEncoder + `rerank(query, candidates, top_k, model=None)`.
- **Create** `backend/tests/unit/test_rerank_service.py` — orden/truncado + fallback (modelo fake/monkeypatch, sin descarga).
- **Modify** `backend/app/services/rag_service.py` — `_semantic_search` (param `query_text`, fetch ancho + rerank); callsite en `query_rag`.
- **Modify** `backend/scripts/run_ragas_eval.py` — callsite `_semantic_search(..., query_text=question)`.
- **Modify** `.env.example` — documentar vars rerank.

---

### Task 1: Dependencia sentence-transformers + rebuild imagen

**Files:** Modify `backend/requirements.txt`

- [ ] **Step 1: Añadir dependencia.** En `backend/requirements.txt`, añadir al final (sin pin estricto; el resolver traerá torch CPU):

```
sentence-transformers
```

- [ ] **Step 2: Rebuild de la imagen backend.**

Run: `docker compose build backend`
Expected: build OK (descarga torch + sentence-transformers; tarda varios minutos, la imagen crece ~2-3GB).

- [ ] **Step 3: Verificar import dentro del contenedor.**

Run: `docker compose run --rm backend python -c "from sentence_transformers import CrossEncoder; print('CE OK')"`
Expected: imprime `CE OK` (sin descargar el modelo todavía — solo importa la lib).

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore(rag): añadir sentence-transformers para re-ranking cross-encoder"
```

---

### Task 2: Config de re-ranking

**Files:** Modify `backend/app/config.py`, `.env.example`

- [ ] **Step 1: Añadir settings.** En `backend/app/config.py`, clase `Settings`, junto a `RAG_TOP_K`/`RAG_SIMILARITY_THRESHOLD`, añadir (match indentación):

```python
    RAG_RERANK: str = "off"            # off | cross_encoder
    RAG_FETCH_K: int = 30              # candidatos recuperados por coseno antes del rerank
    RAG_FETCH_THRESHOLD: float = 0.50  # umbral laxo para el pool de candidatos (recall)
    RERANK_MODEL: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
```

- [ ] **Step 2: Documentar en `.env.example`.** Bajo el bloque `RAG_*`, añadir:

```
# Re-ranking (Iteración 1). off → retrieval por coseno puro (comportamiento base).
# cross_encoder → recupera RAG_FETCH_K candidatos (umbral RAG_FETCH_THRESHOLD) y
# reordena con RERANK_MODEL, devolviendo RAG_TOP_K. Verificar tag en HuggingFace.
RAG_RERANK=off
RAG_FETCH_K=30
RAG_FETCH_THRESHOLD=0.50
RERANK_MODEL=cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
```

- [ ] **Step 3: Verificar carga de settings.**

Run: `docker compose run --rm backend python -c "from app.config import settings; print(settings.RAG_RERANK, settings.RAG_FETCH_K, settings.RERANK_MODEL)"`
Expected: `off 30 cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`

- [ ] **Step 4: Commit**

```bash
git add backend/app/config.py .env.example
git commit -m "feat(rag): config de re-ranking (RAG_RERANK, RAG_FETCH_K, RERANK_MODEL)"
```

---

### Task 3: rerank_service (TDD)

**Files:** Create `backend/app/services/rerank_service.py`, Test `backend/tests/unit/test_rerank_service.py`

- [ ] **Step 1: Escribir tests que fallan.** Crear `backend/tests/unit/test_rerank_service.py`:

```python
from app.services import rerank_service


class FakeCE:
    def __init__(self, scores):
        self._scores = scores

    def predict(self, pairs):
        return self._scores[: len(pairs)]


def test_rerank_orders_by_score_and_truncates():
    cands = [{"content": "a"}, {"content": "b"}, {"content": "c"}]
    ranked = rerank_service.rerank("q", cands, top_k=2, model=FakeCE([0.1, 0.9, 0.5]))
    assert [c["content"] for c in ranked] == ["b", "c"]
    assert ranked[0]["rerank_score"] == 0.9


def test_rerank_empty_candidates():
    assert rerank_service.rerank("q", [], top_k=5, model=FakeCE([])) == []


def test_rerank_fallback_when_model_unavailable(monkeypatch):
    monkeypatch.setattr(rerank_service, "_get_model", lambda: None)
    cands = [{"content": "a"}, {"content": "b"}, {"content": "c"}]
    ranked = rerank_service.rerank("q", cands, top_k=2)
    assert [c["content"] for c in ranked] == ["a", "b"]
```

- [ ] **Step 2: Run, verify fail.**

Run: `docker compose run --rm backend pytest tests/unit/test_rerank_service.py -v`
Expected: FAIL `ModuleNotFoundError: No module named 'app.services.rerank_service'`.

- [ ] **Step 3: Implementar.** Crear `backend/app/services/rerank_service.py`:

```python
"""rerank_service.py — Re-ranking de candidatos con cross-encoder multilingüe.
Lazy-load + config-gated. Fallback a orden original si el modelo no carga."""
from __future__ import annotations

from app.config import settings
from app.utils.logger import logger

_model = None
_load_failed = False


def _get_model():
    global _model, _load_failed
    if _model is not None or _load_failed:
        return _model
    try:
        from sentence_transformers import CrossEncoder
        _model = CrossEncoder(settings.RERANK_MODEL)
        logger.info(f"Cross-encoder cargado: {settings.RERANK_MODEL}")
    except Exception as e:
        _load_failed = True
        logger.warning(f"No se pudo cargar cross-encoder ({e}); rerank desactivado")
    return _model


def rerank(query: str, candidates: list[dict], top_k: int, model=None) -> list[dict]:
    """Reordena `candidates` (cada uno dict con clave 'content') por relevancia
    query↔content y devuelve los top_k. Si no hay modelo, devuelve el orden
    original truncado a top_k."""
    if not candidates:
        return []
    m = model if model is not None else _get_model()
    if m is None:
        return candidates[:top_k]
    pairs = [(query, c["content"]) for c in candidates]
    scores = m.predict(pairs)
    ranked = sorted(zip(candidates, scores), key=lambda x: float(x[1]), reverse=True)
    return [{**cand, "rerank_score": float(score)} for cand, score in ranked[:top_k]]
```

- [ ] **Step 4: Run, verify pass.**

Run: `docker compose run --rm backend pytest tests/unit/test_rerank_service.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/rerank_service.py backend/tests/unit/test_rerank_service.py
git commit -m "feat(rag): rerank_service con cross-encoder lazy + fallback"
```

---

### Task 4: Cablear rerank en `_semantic_search` + callsites

**Files:** Modify `backend/app/services/rag_service.py`, `backend/scripts/run_ragas_eval.py`

- [ ] **Step 1: Reemplazar `_semantic_search`** en `backend/app/services/rag_service.py`. La firma gana `query_text`. Cuando `RAG_RERANK=cross_encoder` y hay `query_text`, recupera `RAG_FETCH_K` candidatos con umbral laxo `RAG_FETCH_THRESHOLD` y reordena a `top_k`; si no, comportamiento idéntico al actual. Reemplazar la función completa por:

```python
async def _semantic_search(
    query_vector: list[float],
    db: AsyncSession,
    top_k: int | None = None,
    threshold: float | None = None,
    query_text: str | None = None,
) -> list[dict]:
    """Cosine similarity search en pgvector, con re-ranking opcional (config-gated)."""
    top_k = top_k or settings.RAG_TOP_K
    rerank_on = settings.RAG_RERANK == "cross_encoder" and query_text is not None

    if rerank_on:
        fetch_k = settings.RAG_FETCH_K
        fetch_threshold = settings.RAG_FETCH_THRESHOLD
    else:
        fetch_k = top_k
        fetch_threshold = threshold or settings.RAG_SIMILARITY_THRESHOLD

    vec_literal = "[" + ",".join(str(v) for v in query_vector) + "]"

    sql = text(f"""
        SELECT
            content,
            metadata AS meta,
            1 - (embedding <=> '{vec_literal}'::vector) AS similarity
        FROM document_chunks
        WHERE 1 - (embedding <=> '{vec_literal}'::vector) >= :threshold
        ORDER BY embedding <=> '{vec_literal}'::vector
        LIMIT :top_k
    """)

    result = await db.execute(sql, {
        "threshold": fetch_threshold,
        "top_k": fetch_k,
    })
    rows = result.fetchall()

    candidates = [
        {
            "content": row.content,
            "metadata": row.meta or {},
            "similarity": float(row.similarity),
        }
        for row in rows
    ]

    if rerank_on and candidates:
        from app.services.rerank_service import rerank
        return rerank(query_text, candidates, top_k)

    return candidates
```

- [ ] **Step 2: Actualizar callsite en `query_rag`.** En la misma `rag_service.py`, cambiar la línea `chunks = await _semantic_search(query_vector, db)` por:

```python
    chunks = await _semantic_search(query_vector, db, query_text=question)
```

- [ ] **Step 3: Actualizar callsite del evaluador.** En `backend/scripts/run_ragas_eval.py`, dentro de `run_rag`, cambiar `chunks = await _semantic_search(query_vec, db)` por:

```python
        chunks = await _semantic_search(query_vec, db, query_text=question)
```

- [ ] **Step 4: Verificar que el comportamiento base (rerank off) no cambió.**

Run: `docker compose exec -T backend pytest tests/unit/ -q`
Expected: toda la suite unit pasa (incl. test_ragas_metrics 15 + test_rerank_service 3). `RAG_RERANK` default `off` ⇒ `_semantic_search` idéntico al anterior.

Run import sanity: `docker compose exec -T backend python -c "import scripts.run_ragas_eval; import app.services.rag_service; print('OK')"` → `OK`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/rag_service.py backend/scripts/run_ragas_eval.py
git commit -m "feat(rag): retrieve-then-rerank en _semantic_search (config-gated)"
```

---

### Task 5: Evaluación iter 1 (rerank on) + latencia + reporte v6 (manual GPU)

**Files:** Create `docs/reporte-RAGAS-v6.md`

- [ ] **Step 1: Descargar el modelo cross-encoder (primera vez).**

Run: `docker compose exec -T backend python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1'); print('modelo OK')"`
Expected: descarga ~120MB y cachea; imprime `modelo OK`. (Verificar antes el tag en HuggingFace.)

- [ ] **Step 2: Medir overhead de latencia del rerank (OE3).**

Run:
```bash
docker compose exec -T backend python -c "
import time, asyncio
from app.services.rerank_service import rerank, _get_model
_get_model()  # warm
cands=[{'content':'texto de prueba '+str(i)} for i in range(30)]
t=time.time(); [rerank('consulta de prueba', cands, 5) for _ in range(10)]; dt=(time.time()-t)/10
print(f'rerank 30→5 promedio: {dt*1000:.0f} ms/query')
"
```
Expected: imprime ms/query. Anotar para OE3 (presupuesto e2e ≤8s).

- [ ] **Step 3: Correr RAGAS iter 1 con rerank on + juez independiente.**

Run: `docker compose exec -T -e RAG_RERANK=cross_encoder -e RAGAS_JUDGE_MODEL=llama3.1:8b backend python scripts/run_ragas_eval.py --iter v6_rerank`
Expected: 50 preguntas; al final las 6 líneas de pass. Genera `scripts/ragas_runs/<ts>_v6_rerank.{csv,summary.json}`.

- [ ] **Step 4: Escribir `docs/reporte-RAGAS-v6.md`** con: config (rerank cross_encoder, fetch_k=30, fetch_threshold=0.50, top_k=7, modelo), tabla de las 6 métricas vs umbral (✓/✗) con Δ vs v5_hardened, latencia rerank medida (Step 2), breakdown por tipo/módulo (copiar del summary.json), y conclusión de qué métricas cerraron. Comparativa v5_hardened → v6.

- [ ] **Step 5: Commit**

```bash
git add docs/reporte-RAGAS-v6.md backend/scripts/ragas_runs/
git commit -m "docs(oe2): RAGAS v6 con re-ranking cross-encoder + latencia"
```

---

## DECISION GATE (tras Task 5)

Leer `docs/reporte-RAGAS-v6.md`:
1. **¿Cumplen las 6?** Si sí → OE2 cerrado; setear `RAG_RERANK=cross_encoder` como default en `.env`/prod y actualizar CLAUDE.md; pasar a finishing-a-development-branch.
2. **¿Siguen cortas recall/faithfulness?** → Iteración 2: chunking semántico 15% + re-index (su propio plan).
3. **¿Latencia rompe OE3?** → bajar `RAG_FETCH_K`, o modelo más liviano, o limitar rerank a contexto de chat (no a otros usos).
4. Protocolo: si una métrica sigue < umbral tras 3 iteraciones (v5, v6, v7) → **detener y consultar al usuario**.

---

## Self-Review

- **Cobertura del baseline:** las 3 métricas que fallan (precision/recall/faithfulness) atacadas por fetch-ancho + rerank (Tasks 3-4). Las 3 que pasan no se degradan (rerank off por default; eval explícito con `-e`).
- **Placeholders:** ninguno en código; `<ts>` y los valores del reporte v6 se llenan con la salida real.
- **Consistencia de tipos:** `rerank(query: str, candidates: list[dict], top_k: int, model=None) -> list[dict]`; `_semantic_search(..., query_text: str|None=None) -> list[dict]`; callsites pasan `query_text=question`. `_get_model()` global lazy. Coinciden entre Task 3 y Task 4.
- **No-rotura:** `RAG_RERANK=off` default ⇒ `_semantic_search` equivale al actual (fetch_k=top_k, fetch_threshold=threshold-or-setting). Tests existentes siguen verdes.
