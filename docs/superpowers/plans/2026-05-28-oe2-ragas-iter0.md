# OE2 RAGAS — Iteración 0 (métricas oficiales + juez independiente) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-instrumentar la evaluación RAGAS para medir las 6 métricas oficiales con un juez LLM independiente del generador y acuerdo Cohen's κ, dejando un re-baseline fiable de las 50 preguntas.

**Architecture:** Extraer las métricas a un módulo aislado y testeable (`ragas_metrics.py`), añadir las 2 métricas faltantes (`context_entities_recall`, `answer_correctness`) y una utilidad de Cohen's κ, hacer el modelo juez configurable (distinto del generador `qwen2.5`), y cablear las 6 métricas + κ + umbrales oficiales en `run_ragas_eval.py`. Todo 100% local (Ollama), sin librería `ragas`, sin APIs pagas.

**Tech Stack:** Python 3.12, pytest + pytest-asyncio, langchain-ollama (ChatOllama/OllamaEmbeddings), numpy. Ejecución de tests dentro del contenedor backend.

**Alcance:** SOLO Iteración 0. La Iteración 1 (retrieve-then-rerank) y la Iteración 2 (chunking semántico) dependen de los datos del re-baseline (Task 7) y tendrán cada una su propio plan tras el Decision Gate al final.

---

## Estructura de archivos

- **Crear** `backend/scripts/ragas_metrics.py` — módulo aislado: helpers de juez (`make_judge`, `make_judge_b`, `make_generator`, `_ainvoke_json`), las 4 métricas actuales, las 2 nuevas, `extract_claims`/`verify_claims`, `cohen_kappa`. Sin imports de DB.
- **Crear** `backend/tests/unit/test_ragas_metrics.py` — tests con `FakeLLM`/`FakeEmbedder` (sin LLM vivo).
- **Modificar** `backend/scripts/run_ragas_eval.py` — importar desde `ragas_metrics`, cablear 6 métricas + κ + umbrales oficiales + None-rate.
- **Modificar** `backend/app/config.py` — `RAGAS_JUDGE_MODEL`, `RAGAS_JUDGE_MODEL_B`.
- **Modificar** `.env.example` — documentar las dos vars nuevas.

---

### Task 1: Extraer `ragas_metrics.py` + tests de regresión

**Files:**
- Create: `backend/scripts/ragas_metrics.py`
- Test: `backend/tests/unit/test_ragas_metrics.py`
- Modify: `backend/scripts/run_ragas_eval.py:35-101` (imports + borrar helpers movidos), `:107-273` (borrar métricas movidas)

- [ ] **Step 1: Escribir el test que falla**

Crear `backend/tests/unit/test_ragas_metrics.py`:

```python
import pytest
from scripts import ragas_metrics as rm


class FakeLLM:
    """Devuelve respuestas .content predefinidas, en orden, por cada ainvoke."""
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    async def ainvoke(self, messages):
        resp = self._responses[self.calls]
        self.calls += 1
        class _M:
            content = resp
        return _M()


class FakeEmbedder:
    def __init__(self, vectors):
        self._vectors = vectors

    async def aembed_documents(self, texts):
        return self._vectors[: len(texts)]


@pytest.mark.asyncio
async def test_faithfulness_half_supported():
    judge = FakeLLM([
        '{"claims": ["c1", "c2"]}',
        '{"verdicts": [{"claim": "c1", "supported": true}, {"claim": "c2", "supported": false}]}',
    ])
    score = await rm.metric_faithfulness(judge, "answer", ["ctx"])
    assert score == 0.5


@pytest.mark.asyncio
async def test_context_recall_all_attributable():
    judge = FakeLLM([
        '{"sentences": ["s1", "s2"]}',
        '{"verdicts": [{"sentence": "s1", "attributable": true}, {"sentence": "s2", "attributable": true}]}',
    ])
    score = await rm.metric_context_recall(judge, "ground truth", ["ctx"])
    assert score == 1.0


@pytest.mark.asyncio
async def test_context_precision_top_ranked_relevant():
    # chunk1 útil, chunk2 no → AP@k = (1/1) / 1 = 1.0
    judge = FakeLLM([
        '{"verdicts": [{"useful": true}, {"useful": false}]}',
    ])
    score = await rm.metric_context_precision(judge, "q", "gt", ["c1", "c2"])
    assert score == 1.0
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `docker compose exec backend pytest tests/unit/test_ragas_metrics.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'scripts.ragas_metrics'`.

- [ ] **Step 3: Crear `ragas_metrics.py` moviendo helpers + 4 métricas**

Crear `backend/scripts/ragas_metrics.py` con este contenido (movido textualmente desde `run_ragas_eval.py`, sin cambiar lógica):

```python
"""ragas_metrics.py — métricas RAGAS-style con juez LLM local. Sin dependencias de DB."""
from __future__ import annotations

import json
import re

import numpy as np
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings

ANSWER_RELEVANCY_N = 2


def make_judge() -> ChatOllama:
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.0,
        num_ctx=4096,
        num_predict=512,
        timeout=settings.OLLAMA_TIMEOUT,
        format="json",
    )


def make_generator() -> ChatOllama:
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.7,
        num_ctx=4096,
        num_predict=256,
        timeout=settings.OLLAMA_TIMEOUT,
        format="json",
    )


async def _ainvoke_json(llm, system: str, human: str) -> dict | None:
    try:
        resp = await llm.ainvoke([
            SystemMessage(content=system),
            HumanMessage(content=human),
        ])
        raw = resp.content.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except Exception as e:
        print(f"  [warn] LLM JSON error: {e}")
        return None


async def metric_faithfulness(judge, answer: str, contexts: list[str]) -> float | None:
    ctx = "\n\n".join(contexts)
    extracted = await _ainvoke_json(
        judge,
        system=(
            "Extrae los claims verificables del texto. Devuelve JSON: "
            '{"claims": ["claim1", "claim2", ...]}. Cada claim es una afirmación '
            "atómica y autónoma. Máximo 8 claims. Ignora saludos u opinión."
        ),
        human=f"Texto:\n{answer}",
    )
    if not extracted or "claims" not in extracted:
        return None
    claims = [str(c).strip() for c in extracted["claims"] if str(c).strip()]
    if not claims:
        return 1.0
    verdict = await _ainvoke_json(
        judge,
        system=(
            "Para cada claim, responde si está respaldado por el CONTEXTO. "
            'Devuelve JSON: {"verdicts": [{"claim": "...", "supported": true|false}, ...]}. '
            "Sé estricto: solo true si el contexto lo afirma explícitamente o lo implica directamente."
        ),
        human=f"CONTEXTO:\n{ctx}\n\nCLAIMS:\n" + "\n".join(f"- {c}" for c in claims),
    )
    if not verdict or "verdicts" not in verdict:
        return None
    verdicts = verdict["verdicts"]
    if not verdicts:
        return None
    supported = 0
    for v in verdicts:
        if isinstance(v, dict):
            if v.get("supported") is True:
                supported += 1
        elif isinstance(v, bool) and v:
            supported += 1
    return round(supported / len(verdicts), 3)


async def metric_answer_relevancy(gen, embedder, question: str, answer: str) -> float | None:
    synth = await _ainvoke_json(
        gen,
        system=(
            f"Dada una respuesta, genera exactamente {ANSWER_RELEVANCY_N} preguntas "
            "diferentes que esa respuesta contestaría. Devuelve JSON: "
            '{"questions": ["q1", "q2"]}. Las preguntas deben ser en español y específicas.'
        ),
        human=f"Respuesta:\n{answer}",
    )
    if not synth or "questions" not in synth:
        return None
    qs = [str(q).strip() for q in synth["questions"] if str(q).strip()]
    if not qs:
        return None
    embs_q = await embedder.aembed_documents([question] + qs)
    orig = np.array(embs_q[0])
    others = np.array(embs_q[1:])

    def cosine(a, b):
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    sims = [cosine(orig, e) for e in others]
    return round(float(np.mean(sims)), 3)


async def metric_context_precision(judge, question: str, ground_truth: str, contexts: list[str]) -> float | None:
    if not contexts:
        return 0.0
    payload = "\n\n".join(f"[Chunk {i+1}]\n{c}" for i, c in enumerate(contexts))
    verdict = await _ainvoke_json(
        judge,
        system=(
            "Dada una PREGUNTA y una RESPUESTA CORRECTA, decide para cada CHUNK "
            "si es útil para responder. Devuelve JSON: "
            '{"verdicts": [{"useful": true|false}, ...]} en el MISMO ORDEN de los chunks.'
        ),
        human=f"PREGUNTA: {question}\nRESPUESTA CORRECTA: {ground_truth}\n\nCHUNKS:\n{payload}",
    )
    if not verdict or "verdicts" not in verdict:
        return None
    vs = verdict["verdicts"]
    useful = []
    for v in vs:
        if isinstance(v, dict):
            useful.append(bool(v.get("useful")))
        elif isinstance(v, bool):
            useful.append(v)
    if not useful:
        return None
    total_rel = sum(useful)
    if total_rel == 0:
        return 0.0
    precision_at_k = []
    hits = 0
    for k, u in enumerate(useful, 1):
        if u:
            hits += 1
            precision_at_k.append(hits / k)
    return round(sum(precision_at_k) / total_rel, 3)


async def metric_context_recall(judge, ground_truth: str, contexts: list[str]) -> float | None:
    ctx = "\n\n".join(contexts)
    extracted = await _ainvoke_json(
        judge,
        system=(
            "Parte el texto en sentencias atómicas. Devuelve JSON: "
            '{"sentences": ["s1", "s2", ...]}. Máximo 8 sentencias.'
        ),
        human=f"Texto:\n{ground_truth}",
    )
    if not extracted or "sentences" not in extracted:
        return None
    sents = [str(s).strip() for s in extracted["sentences"] if str(s).strip()]
    if not sents:
        return 1.0
    verdict = await _ainvoke_json(
        judge,
        system=(
            "Para cada SENTENCIA, responde si está respaldada por el CONTEXTO. "
            'Devuelve JSON: {"verdicts": [{"sentence": "...", "attributable": true|false}, ...]}. '
            "Sé estricto."
        ),
        human=f"CONTEXTO:\n{ctx}\n\nSENTENCIAS:\n" + "\n".join(f"- {s}" for s in sents),
    )
    if not verdict or "verdicts" not in verdict:
        return None
    vs = verdict["verdicts"]
    if not vs:
        return None
    attr = 0
    for v in vs:
        if isinstance(v, dict):
            if v.get("attributable") is True:
                attr += 1
        elif isinstance(v, bool) and v:
            attr += 1
    return round(attr / len(vs), 3)
```

- [ ] **Step 4: Modificar `run_ragas_eval.py` para importar desde el módulo**

En `run_ragas_eval.py`, borrar las definiciones de `make_judge`, `make_generator`, `_ainvoke_json` y las 4 funciones `metric_*` (líneas ~58-273), y añadir tras los imports existentes (después de la línea 46 `import redis.asyncio as aioredis`):

```python
from scripts.ragas_metrics import (
    make_judge,
    make_generator,
    metric_faithfulness,
    metric_answer_relevancy,
    metric_context_precision,
    metric_context_recall,
)
```

Mantener el resto de `run_ragas_eval.py` igual.

- [ ] **Step 5: Correr tests y verificar que pasan**

Run: `docker compose exec backend pytest tests/unit/test_ragas_metrics.py -v`
Expected: PASS (3 tests).

- [ ] **Step 6: Commit**

```bash
git add backend/scripts/ragas_metrics.py backend/tests/unit/test_ragas_metrics.py backend/scripts/run_ragas_eval.py
git commit -m "refactor(ragas): extraer métricas a ragas_metrics.py con tests de regresión"
```

---

### Task 2: Métrica `context_entities_recall`

**Files:**
- Modify: `backend/scripts/ragas_metrics.py` (añadir función al final)
- Test: `backend/tests/unit/test_ragas_metrics.py` (añadir tests)

- [ ] **Step 1: Escribir el test que falla**

Añadir a `test_ragas_metrics.py`:

```python
@pytest.mark.asyncio
async def test_context_entities_recall_half_present():
    judge = FakeLLM([
        '{"entities": ["Retrofit", "Coroutine"]}',
        '{"verdicts": [{"entity": "Retrofit", "present": true}, {"entity": "Coroutine", "present": false}]}',
    ])
    score = await rm.metric_context_entities_recall(judge, "ground truth", ["ctx"])
    assert score == 0.5


@pytest.mark.asyncio
async def test_context_entities_recall_no_entities_returns_one():
    judge = FakeLLM(['{"entities": []}'])
    score = await rm.metric_context_entities_recall(judge, "ground truth", ["ctx"])
    assert score == 1.0
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `docker compose exec backend pytest tests/unit/test_ragas_metrics.py -k entities -v`
Expected: FAIL con `AttributeError: module 'scripts.ragas_metrics' has no attribute 'metric_context_entities_recall'`.

- [ ] **Step 3: Implementar la métrica**

Añadir al final de `ragas_metrics.py`:

```python
async def metric_context_entities_recall(judge, ground_truth: str, contexts: list[str]) -> float | None:
    """Fracción de entidades del ground_truth presentes en el contexto recuperado."""
    ctx = "\n\n".join(contexts)
    extracted = await _ainvoke_json(
        judge,
        system=(
            "Extrae las entidades clave del texto: términos técnicos, nombres de "
            "clases/funciones/APIs, conceptos propios del dominio. Devuelve JSON: "
            '{"entities": ["e1", "e2", ...]}. Máximo 10 entidades. Sin duplicados.'
        ),
        human=f"Texto:\n{ground_truth}",
    )
    if not extracted or "entities" not in extracted:
        return None
    entities = [str(e).strip() for e in extracted["entities"] if str(e).strip()]
    if not entities:
        return 1.0
    verdict = await _ainvoke_json(
        judge,
        system=(
            "Para cada ENTIDAD, responde si aparece (literalmente o por sinónimo "
            'directo) en el CONTEXTO. Devuelve JSON: {"verdicts": '
            '[{"entity": "...", "present": true|false}, ...]}.'
        ),
        human=f"CONTEXTO:\n{ctx}\n\nENTIDADES:\n" + "\n".join(f"- {e}" for e in entities),
    )
    if not verdict or "verdicts" not in verdict:
        return None
    vs = verdict["verdicts"]
    if not vs:
        return None
    present = sum(1 for v in vs if isinstance(v, dict) and v.get("present") is True)
    return round(present / len(vs), 3)
```

- [ ] **Step 4: Correr tests y verificar que pasan**

Run: `docker compose exec backend pytest tests/unit/test_ragas_metrics.py -k entities -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/scripts/ragas_metrics.py backend/tests/unit/test_ragas_metrics.py
git commit -m "feat(ragas): añadir métrica context_entities_recall"
```

---

### Task 3: Métrica `answer_correctness`

**Files:**
- Modify: `backend/scripts/ragas_metrics.py` (añadir función al final)
- Test: `backend/tests/unit/test_ragas_metrics.py` (añadir tests)

- [ ] **Step 1: Escribir el test que falla**

Añadir a `test_ragas_metrics.py`:

```python
@pytest.mark.asyncio
async def test_answer_correctness_perfect():
    # tp=2, fp=0, fn=0 → F1=1.0 ; embeddings idénticos → coseno=1.0 → 0.75+0.25=1.0
    judge = FakeLLM(['{"tp": 2, "fp": 0, "fn": 0}'])
    embedder = FakeEmbedder([[1.0, 0.0], [1.0, 0.0]])
    score = await rm.metric_answer_correctness(judge, embedder, "answer", "ground truth")
    assert score == 1.0


@pytest.mark.asyncio
async def test_answer_correctness_partial():
    # tp=1, fp=1, fn=1 → F1 = 1/(1+0.5*2)=0.5 ; coseno=0 → 0.75*0.5 = 0.375
    judge = FakeLLM(['{"tp": 1, "fp": 1, "fn": 1}'])
    embedder = FakeEmbedder([[1.0, 0.0], [0.0, 1.0]])
    score = await rm.metric_answer_correctness(judge, embedder, "answer", "ground truth")
    assert score == 0.375
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `docker compose exec backend pytest tests/unit/test_ragas_metrics.py -k correctness -v`
Expected: FAIL con `AttributeError: ... has no attribute 'metric_answer_correctness'`.

- [ ] **Step 3: Implementar la métrica**

Añadir al final de `ragas_metrics.py`:

```python
async def metric_answer_correctness(judge, embedder, answer: str, ground_truth: str) -> float | None:
    """RAGAS-style: 0.75·F1_factual + 0.25·coseno(answer, ground_truth)."""
    classified = await _ainvoke_json(
        judge,
        system=(
            "Compara una RESPUESTA con la RESPUESTA CORRECTA. Cuenta las afirmaciones:\n"
            "- TP: presentes en RESPUESTA y respaldadas por RESPUESTA CORRECTA\n"
            "- FP: presentes en RESPUESTA pero NO en RESPUESTA CORRECTA\n"
            "- FN: presentes en RESPUESTA CORRECTA pero ausentes en RESPUESTA\n"
            'Devuelve JSON: {"tp": n, "fp": n, "fn": n} (enteros).'
        ),
        human=f"RESPUESTA:\n{answer}\n\nRESPUESTA CORRECTA:\n{ground_truth}",
    )
    if not classified:
        return None
    try:
        tp = int(classified.get("tp", 0))
        fp = int(classified.get("fp", 0))
        fn = int(classified.get("fn", 0))
    except (TypeError, ValueError, AttributeError):
        return None
    denom = tp + 0.5 * (fp + fn)
    f1 = (tp / denom) if denom > 0 else 0.0
    embs = await embedder.aembed_documents([answer, ground_truth])
    a, g = np.array(embs[0]), np.array(embs[1])
    na, ng = np.linalg.norm(a), np.linalg.norm(g)
    sem = float(np.dot(a, g) / (na * ng)) if na and ng else 0.0
    return round(0.75 * f1 + 0.25 * sem, 3)
```

- [ ] **Step 4: Correr tests y verificar que pasan**

Run: `docker compose exec backend pytest tests/unit/test_ragas_metrics.py -k correctness -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/scripts/ragas_metrics.py backend/tests/unit/test_ragas_metrics.py
git commit -m "feat(ragas): añadir métrica answer_correctness (F1 factual + coseno)"
```

---

### Task 4: Cohen's κ + split `extract_claims`/`verify_claims`

**Files:**
- Modify: `backend/scripts/ragas_metrics.py` (añadir `cohen_kappa`, `extract_claims`, `verify_claims`; refactor `metric_faithfulness` para componerlas)
- Test: `backend/tests/unit/test_ragas_metrics.py` (añadir tests)

- [ ] **Step 1: Escribir el test que falla**

Añadir a `test_ragas_metrics.py`:

```python
def test_cohen_kappa_perfect_agreement():
    assert rm.cohen_kappa([True, False, True, False], [True, False, True, False]) == 1.0


def test_cohen_kappa_known_value():
    # a=[T,T,F,F], b=[T,F,F,F]: po=0.75, pa_true=0.5, pb_true=0.25
    # pe = 0.5*0.25 + 0.5*0.75 = 0.5 ; κ = (0.75-0.5)/(1-0.5) = 0.5
    assert rm.cohen_kappa([True, True, False, False], [True, False, False, False]) == 0.5


@pytest.mark.asyncio
async def test_verify_claims_labels():
    judge = FakeLLM(['{"verdicts": [{"claim": "c1", "supported": true}, {"claim": "c2", "supported": false}]}'])
    labels = await rm.verify_claims(judge, ["c1", "c2"], ["ctx"])
    assert labels == [True, False]
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `docker compose exec backend pytest tests/unit/test_ragas_metrics.py -k "kappa or verify_claims" -v`
Expected: FAIL con `AttributeError: ... has no attribute 'cohen_kappa'`.

- [ ] **Step 3: Implementar κ + el split, y recomponer faithfulness**

Añadir a `ragas_metrics.py`:

```python
def cohen_kappa(labels_a: list[bool], labels_b: list[bool]) -> float:
    """Cohen's κ para dos listas de etiquetas binarias pareadas."""
    n = len(labels_a)
    if n == 0 or n != len(labels_b):
        raise ValueError("las listas de etiquetas deben tener el mismo tamaño no-nulo")
    po = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n
    pa = sum(1 for a in labels_a if a) / n
    pb = sum(1 for b in labels_b if b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    if pe == 1.0:
        return 1.0
    return round((po - pe) / (1 - pe), 3)


async def extract_claims(judge, answer: str) -> list[str] | None:
    extracted = await _ainvoke_json(
        judge,
        system=(
            "Extrae los claims verificables del texto. Devuelve JSON: "
            '{"claims": ["claim1", "claim2", ...]}. Cada claim es una afirmación '
            "atómica y autónoma. Máximo 8 claims. Ignora saludos u opinión."
        ),
        human=f"Texto:\n{answer}",
    )
    if not extracted or "claims" not in extracted:
        return None
    return [str(c).strip() for c in extracted["claims"] if str(c).strip()]


async def verify_claims(judge, claims: list[str], contexts: list[str]) -> list[bool] | None:
    if not claims:
        return []
    ctx = "\n\n".join(contexts)
    verdict = await _ainvoke_json(
        judge,
        system=(
            "Para cada claim, responde si está respaldado por el CONTEXTO. "
            'Devuelve JSON: {"verdicts": [{"claim": "...", "supported": true|false}, ...]}. '
            "Sé estricto: solo true si el contexto lo afirma explícitamente o lo implica directamente."
        ),
        human=f"CONTEXTO:\n{ctx}\n\nCLAIMS:\n" + "\n".join(f"- {c}" for c in claims),
    )
    if not verdict or "verdicts" not in verdict:
        return None
    out = []
    for v in verdict["verdicts"]:
        if isinstance(v, dict):
            out.append(v.get("supported") is True)
        elif isinstance(v, bool):
            out.append(v)
    return out
```

Reemplazar el cuerpo de `metric_faithfulness` por esta composición (mismo comportamiento observable):

```python
async def metric_faithfulness(judge, answer: str, contexts: list[str]) -> float | None:
    claims = await extract_claims(judge, answer)
    if claims is None:
        return None
    if not claims:
        return 1.0
    labels = await verify_claims(judge, claims, contexts)
    if not labels:
        return None
    return round(sum(1 for x in labels if x) / len(labels), 3)
```

- [ ] **Step 4: Correr toda la suite del módulo y verificar que pasa**

Run: `docker compose exec backend pytest tests/unit/test_ragas_metrics.py -v`
Expected: PASS (todos, incl. `test_faithfulness_half_supported` que protege la recomposición).

- [ ] **Step 5: Commit**

```bash
git add backend/scripts/ragas_metrics.py backend/tests/unit/test_ragas_metrics.py
git commit -m "feat(ragas): cohen_kappa + split extract/verify_claims para κ inter-juez"
```

---

### Task 5: Juez independiente configurable

**Files:**
- Modify: `backend/app/config.py` (clase `Settings`, junto a `OLLAMA_MODEL`)
- Modify: `backend/scripts/ragas_metrics.py` (`make_judge`, nuevo `make_judge_b`)
- Modify: `.env.example` (sección OLLAMA)
- Test: `backend/tests/unit/test_ragas_metrics.py`

- [ ] **Step 1: Escribir el test que falla**

Añadir a `test_ragas_metrics.py`:

```python
def test_make_judge_uses_configured_model(monkeypatch):
    monkeypatch.setattr(rm.settings, "RAGAS_JUDGE_MODEL", "llama3.1:8b")
    judge = rm.make_judge()
    assert judge.model == "llama3.1:8b"


def test_make_judge_falls_back_to_generator(monkeypatch):
    monkeypatch.setattr(rm.settings, "RAGAS_JUDGE_MODEL", "")
    judge = rm.make_judge()
    assert judge.model == rm.settings.OLLAMA_MODEL
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `docker compose exec backend pytest tests/unit/test_ragas_metrics.py -k make_judge -v`
Expected: FAIL — `AttributeError: 'Settings' object has no attribute 'RAGAS_JUDGE_MODEL'`.

- [ ] **Step 3: Añadir las settings**

En `backend/app/config.py`, dentro de la clase `Settings`, junto al campo `OLLAMA_MODEL`, añadir:

```python
    RAGAS_JUDGE_MODEL: str = ""       # juez independiente; vacío → usa OLLAMA_MODEL
    RAGAS_JUDGE_MODEL_B: str = ""     # 2º juez para Cohen's κ; vacío → sin κ
```

- [ ] **Step 4: Actualizar `make_judge` y añadir `make_judge_b` en `ragas_metrics.py`**

Reemplazar `make_judge` por:

```python
def make_judge(model: str | None = None) -> ChatOllama:
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=model or settings.RAGAS_JUDGE_MODEL or settings.OLLAMA_MODEL,
        temperature=0.0,
        num_ctx=4096,
        num_predict=512,
        timeout=settings.OLLAMA_TIMEOUT,
        format="json",
    )


def make_judge_b() -> ChatOllama | None:
    """2º juez para κ. None si RAGAS_JUDGE_MODEL_B no está configurado."""
    if not settings.RAGAS_JUDGE_MODEL_B:
        return None
    return make_judge(model=settings.RAGAS_JUDGE_MODEL_B)
```

- [ ] **Step 5: Documentar las vars en `.env.example`**

En `.env.example`, bajo el bloque `OLLAMA_*`, añadir:

```
# Juez RAGAS independiente del generador (reduce sesgo de auto-preferencia).
# Verificar el tag oficial en ollama.com y hacer `ollama pull` antes de usar.
RAGAS_JUDGE_MODEL=        # ej. llama3.1:8b-instruct-q4_K_M  (vacío → usa OLLAMA_MODEL)
RAGAS_JUDGE_MODEL_B=      # 2º juez para Cohen's κ (vacío → sin κ)
```

- [ ] **Step 6: Correr tests y verificar que pasan**

Run: `docker compose exec backend pytest tests/unit/test_ragas_metrics.py -k make_judge -v`
Expected: PASS (2 tests).

- [ ] **Step 7: Commit**

```bash
git add backend/app/config.py backend/scripts/ragas_metrics.py .env.example
git commit -m "feat(ragas): juez LLM configurable e independiente del generador"
```

---

### Task 6: Cablear 6 métricas + umbrales oficiales + κ + None-rate en el runner

**Files:**
- Modify: `backend/scripts/run_ragas_eval.py` (imports, loop principal, summary)

- [ ] **Step 1: Ampliar imports**

En `run_ragas_eval.py`, ampliar el import de `ragas_metrics` (Task 1, Step 4) a:

```python
from scripts.ragas_metrics import (
    make_judge,
    make_judge_b,
    make_generator,
    metric_faithfulness,
    metric_answer_relevancy,
    metric_context_precision,
    metric_context_recall,
    metric_context_entities_recall,
    metric_answer_correctness,
    extract_claims,
    verify_claims,
    cohen_kappa,
)
```

- [ ] **Step 2: Añadir columnas y juez B**

En `main()`, tras `judge = make_judge()` (≈línea 316), añadir:

```python
    judge_b = make_judge_b()
    kappa_a: list[bool] = []
    kappa_b: list[bool] = []
```

En `fieldnames` (≈línea 333), añadir `"context_entities_recall"` y `"answer_correctness"` después de `"context_recall"`.

En el dict `row` inicial (≈línea 346) añadir:

```python
                "context_entities_recall": None,
                "answer_correctness": None,
```

- [ ] **Step 3: Calcular las 2 nuevas métricas + acumular κ**

Dentro del bloque `if contexts:` (≈línea 366-373), tras `row["context_recall"] = ...`, añadir:

```python
                    row["context_entities_recall"] = await metric_context_entities_recall(
                        judge, q["ground_truth"], contexts
                    )
                    if judge_b is not None:
                        claims = await extract_claims(judge, answer)
                        if claims:
                            la = await verify_claims(judge, claims, contexts)
                            lb = await verify_claims(judge_b, claims, contexts)
                            if la and lb and len(la) == len(lb):
                                kappa_a.extend(la)
                                kappa_b.extend(lb)
```

Tras el cálculo de `answer_relevancy` (≈línea 374-376), añadir:

```python
                row["answer_correctness"] = await metric_answer_correctness(
                    judge, embedder, answer, q["ground_truth"]
                )
```

- [ ] **Step 4: Actualizar el print de progreso y el summary**

En la tupla del `metrics_str` (≈línea 388) cambiar a las 6 métricas:

```python
                for k in ("faithfulness", "answer_relevancy", "context_precision",
                          "context_recall", "context_entities_recall", "answer_correctness")
```

Reemplazar el dict `summary` (≈líneas 398-424) por:

```python
    OFFICIAL = {
        "faithfulness": 0.80,
        "answer_relevancy": 0.75,
        "context_precision": 0.70,
        "context_recall": 0.75,
        "context_entities_recall": 0.70,
        "answer_correctness": 0.70,
    }

    def none_rate(key):
        total = len(results)
        nones = sum(1 for r in results if r[key] is None)
        return round(nones / total, 3) if total else None

    kappa = cohen_kappa(kappa_a, kappa_b) if kappa_a else None

    summary = {
        "label": label,
        "timestamp": stamp,
        "n_questions": len(questions),
        "config": {
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP,
            "threshold": settings.RAG_SIMILARITY_THRESHOLD,
            "top_k": settings.RAG_TOP_K,
            "llm": settings.OLLAMA_MODEL,
            "judge": settings.RAGAS_JUDGE_MODEL or settings.OLLAMA_MODEL,
            "judge_b": settings.RAGAS_JUDGE_MODEL_B or None,
            "embed": settings.OLLAMA_EMBED_MODEL,
        },
        "global": {k: avg(k) for k in OFFICIAL},
        "none_rate": {k: none_rate(k) for k in OFFICIAL},
        "thresholds": OFFICIAL,
        "kappa_faithfulness_verdicts": kappa,
        "pass": {k: (avg(k) or 0) >= OFFICIAL[k] for k in OFFICIAL},
    }
```

En el breakdown por dimensión (≈líneas 435-441), añadir al dict `breakdown[b]`:

```python
                "context_entities_recall": bavg("context_entities_recall"),
                "answer_correctness": bavg("answer_correctness"),
```

Reemplazar los dos `print` finales de pass (≈líneas 451-452) por:

```python
    for k in OFFICIAL:
        ok = "✓" if summary["pass"][k] else "✗"
        print(f"{k} ≥ {OFFICIAL[k]:.2f}  ·  {ok}  (valor={summary['global'][k]}, none_rate={summary['none_rate'][k]})")
    if kappa is not None:
        print(f"Cohen's κ (faithfulness verdicts, juez A vs B): {kappa}")
```

- [ ] **Step 5: Smoke test del runner (2 preguntas, requiere Ollama+DB)**

Run: `docker compose exec backend python scripts/run_ragas_eval.py --max 2 --iter v5_smoke`
Expected: corre 2 preguntas sin excepción; imprime las **6** líneas de pass; genera `scripts/ragas_runs/<ts>_v5_smoke.summary.json` con claves `global` (6 métricas), `none_rate`, `thresholds`, `pass`.

> Si Ollama o la DB no están arriba: `docker compose up -d` primero. Esto NO es un unit test; valida el cableado end-to-end.

- [ ] **Step 6: Commit**

```bash
git add backend/scripts/run_ragas_eval.py
git commit -m "feat(ragas): 6 métricas oficiales + umbrales + κ + none_rate en runner"
```

---

### Task 7: Re-baseline v5 (manual, requiere GPU) + registro

**Files:**
- Modify: `.env` (local, NO commitear) — set `RAGAS_JUDGE_MODEL`, `RAGAS_JUDGE_MODEL_B`
- Create: `docs/reporte-RAGAS-v5.md` (registro del re-baseline)

- [ ] **Step 1: Verificar tag oficial + pull del juez independiente**

⚠️ Verificar el tag exacto en ollama.com antes de pull. Ejemplo (confirmar):

Run: `ollama pull llama3.1:8b` (nativo Windows) y opcionalmente un 2º juez `ollama pull gemma2:9b` para κ.
Expected: descarga completa; `ollama list` los muestra.

- [ ] **Step 2: Configurar el juez en `.env`**

En `.env` (local), set:

```
RAGAS_JUDGE_MODEL=llama3.1:8b
RAGAS_JUDGE_MODEL_B=gemma2:9b
```

(usar los tags reales verificados en Step 1)

- [ ] **Step 3: Correr la evaluación completa (50 preguntas)**

Run: `docker compose exec backend python scripts/run_ragas_eval.py --iter v5_baseline`
Expected: 50 preguntas; al final, las 6 líneas de pass + κ. Tiempo: minutos (depende de GPU). Genera `scripts/ragas_runs/<ts>_v5_baseline.{csv,summary.json}`.

- [ ] **Step 4: Registrar resultados**

Crear `docs/reporte-RAGAS-v5.md` con: tabla de las 6 métricas vs umbral (✓/✗), κ, none_rate por métrica, breakdown por módulo/tipo/dificultad (copiar del summary.json), y una nota de qué métricas siguen cortas. Plantilla:

```markdown
# Reporte RAGAS v5 — re-baseline bajo umbrales oficiales

**Fecha:** <hoy> · **Juez:** <RAGAS_JUDGE_MODEL> · **Juez B (κ):** <RAGAS_JUDGE_MODEL_B> · **Generador:** qwen2.5:7b-instruct-q4_K_M

| Métrica | Umbral | v5 | Estado |
|---|---|---|---|
| faithfulness | 0.80 | <val> | <✓/✗> |
| answer_relevancy | 0.75 | <val> | <✓/✗> |
| context_precision | 0.70 | <val> | <✓/✗> |
| context_recall | 0.75 | <val> | <✓/✗> |
| context_entities_recall | 0.70 | <val> | <✓/✗> |
| answer_correctness | 0.70 | <val> | <✓/✗> |

Cohen's κ (faithfulness verdicts, A vs B): <val>

## None-rate por métrica
<copiar de summary.json>

## Breakdown
<copiar de summary.json: by_module / by_type / by_difficulty>

## Métricas que siguen < umbral
<lista → entra como input al Decision Gate / Iteración 1>
```

- [ ] **Step 5: Commit (solo el reporte; NO el .env)**

```bash
git add docs/reporte-RAGAS-v5.md backend/scripts/ragas_runs/
git commit -m "docs(oe2): re-baseline RAGAS v5 con métricas oficiales + juez independiente"
```

---

## DECISION GATE (tras Task 7)

Leer `docs/reporte-RAGAS-v5.md`. Decidir con datos:

1. **¿Qué métricas siguen < umbral?** Si solo faltan precision/recall → Iteración 1 (rerank). Si faithfulness sigue corta → el rerank suele ayudar (menos ruido en contexto); confirmar.
2. **Elegir reranker** (cross-encoder vs LLM-rerank vs MMR) según cuán lejos esté precision y el costo aceptable.
3. **¿Iteración 2 (chunking semántico) necesaria?** Solo si recall/faithfulness siguen cortas tras rerank.

→ Cada iteración siguiente obtiene su **propio plan** (brainstorming ya cubrió el diseño staged; el plan de iter 1 se escribe aquí con el reranker ya elegido). Protocolo: si una métrica sigue < umbral tras 3 iteraciones → detener y consultar al usuario.

---

## Self-Review (hecho)

- **Cobertura del spec:** §5.1 métricas → Tasks 1-3; §5.2 juez+κ → Tasks 4-5 + wiring Task 6; §5.3 retrieval → fuera de iter 0 (Decision Gate, por diseño staged); §5.4 chunking → fuera de iter 0; §7 errores (None-rate, fail-fast modelo) → Task 6 Step 4 + Task 7 Step 1; §8 testing → Tasks 1-5 TDD; §9 protocolo → Task 7 + Decision Gate.
- **Placeholders:** ninguno en código; los `<val>` del reporte v5 se rellenan con la salida real del run (no es código).
- **Consistencia de tipos:** `metric_*(judge, ...) -> float|None`, `extract_claims -> list[str]|None`, `verify_claims -> list[bool]|None`, `cohen_kappa(list[bool], list[bool]) -> float`, `make_judge(model=None)`, `make_judge_b() -> ChatOllama|None`. Nombres usados en Task 6 coinciden con definiciones de Tasks 1-5.
