# Companion «El sistema sigue al estudiante» (Fase 5) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Endpoint determinista `GET /tutor/companion` (posición del estudiante + diagnóstico por módulo + saludo + recursos) que alimenta el panel «Tu ruta» del Dashboard, la burbuja preview del FloatingTutor y la franja de diagnóstico en ModuleDetail.

**Architecture:** Nuevo `companion_service.py` con funciones puras (`pick_current_index`, `build_diagnostic`, `build_greeting`) + un gather desde BD que reutiliza el invariante `module_service.compute_locks`. Un solo payload cacheado en Redis (TTL 60s) alimenta las 3 superficies frontend vía hook `useCompanion()`. Sin LLM. Fuera de la matriz ISO (los 33 RF quedan congelados; tests nuevos son adicionales).

**Tech Stack:** FastAPI + SQLAlchemy 2.0 async + Pydantic v2 + Redis (`app/utils/cache.cached_json`) · React 18 + TS + TanStack Query + Tailwind tokens semánticos · pytest (mock-db conftest) + Vitest/RTL.

**Spec:** `docs/superpowers/specs/2026-06-09-companion-seguimiento-design.md` · **Rama:** `feat/companion-seguimiento` (ya creada).

**Convenciones que el ejecutor debe respetar:**
- Código en inglés, strings de UI en español peruano, docstrings en español (patrón de `tutor_service.py`).
- Comandos backend se corren desde `backend/`: `python -m pytest ...` (PowerShell: `cd C:\tutor-ia-rfa\backend; python -m pytest ...`).
- Comandos frontend desde `frontend/`: `npx vitest run ...` y `npx tsc --noEmit`.
- Scores de quiz/coding están en escala 0-100 (misma convención que Fase 4 `_result_nudges`).

---

### Task 1: Schemas Pydantic + dataclass de entrada

**Files:**
- Create: `backend/app/schemas/companion.py`

- [ ] **Step 1: Crear el archivo de schemas completo**

```python
"""schemas/companion.py — Posición del estudiante + diagnóstico por módulo (Fase 5, sin LLM)."""
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from app.schemas.learning_resource import LearningResourceResponse


class TopicDiagnostic(BaseModel):
    topic_id: int
    title: str
    best_score: float | None
    attempts: int


class NextAction(BaseModel):
    kind: Literal["retry_quiz", "next_topic", "coding_challenge", "module"]
    label: str
    route: str


class ModuleDiagnostic(BaseModel):
    weak: list[TopicDiagnostic]       # repasar: score <60 o ≥2 intentos fallidos (y <80)
    practice: list[TopicDiagnostic]   # afianzar: mejor score en [60, 80)
    next_action: NextAction


class CompanionPosition(BaseModel):
    module_id: int
    module_title: str
    icon_name: str | None
    color_hex: str | None
    progress_pct: float
    topics_done: int
    topics_total: int
    course_completed: bool


class CompanionResponse(BaseModel):
    needs_assessment: bool
    position: CompanionPosition | None
    greeting: str
    diagnostic: ModuleDiagnostic | None
    resources: list[LearningResourceResponse]


@dataclass
class TopicStat:
    """Stats de un tema del módulo actual ya resueltos desde BD; insumo puro de build_diagnostic."""
    topic_id: int
    title: str
    order_index: int
    visited: bool
    completed: bool
    best_score: float | None   # mejor score de quiz (0-100), None si nunca intentó
    attempts: int
    failed_attempts: int
    has_coding_pending: bool   # hay desafío de catálogo sin aprobar (≥60) en este tema
```

- [ ] **Step 2: Verificar que importa sin errores**

Run: `cd C:\tutor-ia-rfa\backend; python -c "from app.schemas.companion import CompanionResponse, TopicStat; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/companion.py
git commit -m "feat(companion): schemas de posicion del estudiante y diagnostico por modulo"
```

---

### Task 2: Funciones puras `pick_current_index` + `build_diagnostic` (TDD)

**Files:**
- Create: `backend/app/services/companion_service.py`
- Test: `backend/tests/unit/test_companion_service.py`

- [ ] **Step 1: Escribir tests que fallan**

Crear `backend/tests/unit/test_companion_service.py`:

```python
"""Unit tests del motor companion (puro, sin BD ni LLM)."""
from app.schemas.companion import CompanionPosition, TopicStat
from app.services.companion_service import build_diagnostic, pick_current_index


def _stat(**over):
    base = dict(
        topic_id=1, title="Tema", order_index=0, visited=True, completed=False,
        best_score=None, attempts=0, failed_attempts=0, has_coding_pending=False,
    )
    base.update(over)
    return TopicStat(**base)


# --- pick_current_index: módulo actual = primer desbloqueado e incompleto ---

def test_pick_current_nothing_started_is_first_module():
    assert pick_current_index([(4, 0), (5, 0)]) == 0


def test_pick_current_mid_course():
    assert pick_current_index([(4, 4), (5, 2), (4, 0)]) == 1


def test_pick_current_all_complete_returns_none():
    assert pick_current_index([(4, 4), (5, 5)]) is None


def test_pick_current_empty_module_is_current():
    # módulo sin temas nunca cuenta como completo (regla de compute_locks)
    assert pick_current_index([(4, 4), (0, 0), (4, 0)]) == 1


# --- build_diagnostic: clasificación por bandas ---

def test_low_score_is_weak_with_retry_action():
    d = build_diagnostic(
        [_stat(topic_id=12, title="Layouts", best_score=45, attempts=2, failed_attempts=2)],
        module_id=3,
    )
    assert [t.topic_id for t in d.weak] == [12]
    assert d.next_action.kind == "retry_quiz"
    assert d.next_action.route == "/topics/12"


def test_two_failed_attempts_is_weak_even_if_passed():
    d = build_diagnostic([_stat(best_score=70, attempts=3, failed_attempts=2)], module_id=3)
    assert len(d.weak) == 1


def test_dominated_score_overrides_failed_attempts():
    d = build_diagnostic([_stat(best_score=90, attempts=3, failed_attempts=2)], module_id=3)
    assert d.weak == [] and d.practice == []


def test_mid_band_is_practice():
    d = build_diagnostic([_stat(best_score=70, attempts=1, failed_attempts=0)], module_id=3)
    assert len(d.practice) == 1 and d.weak == []


def test_unvisited_topic_is_next_action():
    d = build_diagnostic(
        [
            _stat(topic_id=1, best_score=85, completed=True),
            _stat(topic_id=2, title="Intents", order_index=1, visited=False),
        ],
        module_id=3,
    )
    assert d.next_action.kind == "next_topic"
    assert d.next_action.route == "/topics/2"


def test_weak_beats_pending_in_priority():
    d = build_diagnostic(
        [
            _stat(topic_id=1, best_score=40, failed_attempts=1),
            _stat(topic_id=2, order_index=1, visited=False),
        ],
        module_id=3,
    )
    assert d.next_action.kind == "retry_quiz"


def test_coding_pending_when_no_weak_nor_pending():
    d = build_diagnostic(
        [_stat(topic_id=1, best_score=85, completed=True, has_coding_pending=True)],
        module_id=3,
    )
    assert d.next_action.kind == "coding_challenge"
    assert d.next_action.route == "/topics/1"


def test_fallback_next_action_is_module():
    d = build_diagnostic([_stat(best_score=85, completed=True)], module_id=3)
    assert d.next_action.kind == "module"
    assert d.next_action.route == "/modules/3"


def test_empty_module_stats():
    d = build_diagnostic([], module_id=3)
    assert d.weak == [] and d.practice == []
    assert d.next_action.kind == "module"
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `cd C:\tutor-ia-rfa\backend; python -m pytest tests/unit/test_companion_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.companion_service'`

- [ ] **Step 3: Implementación mínima**

Crear `backend/app/services/companion_service.py`:

```python
"""services/companion_service.py — Posición del estudiante + diagnóstico determinista (Fase 5).

El sistema «sigue» al estudiante: pick_current_index/build_diagnostic/build_greeting
son funciones puras (sin BD ni LLM). gather_companion resuelve el estado desde BD
reutilizando el invariante de desbloqueo secuencial de module_service.compute_locks.
"""
from app.schemas.companion import (
    CompanionPosition,
    ModuleDiagnostic,
    NextAction,
    TopicDiagnostic,
    TopicStat,
)
from app.services.module_service import compute_locks

# Bandas de diagnóstico sobre el mejor score de quiz (0-100)
WEAK_SCORE = 60.0        # < 60 → repasar
PRACTICE_SCORE = 80.0    # [60, 80) → afianzar · ≥ 80 → dominado
WEAK_FAILED_ATTEMPTS = 2  # ≥ 2 intentos fallidos (sin dominar) → repasar
CODING_PASS_SCORE = 60.0  # submission ≥ 60 da el desafío por resuelto
MAX_RESOURCES = 3


def pick_current_index(progress_pairs: list[tuple[int, int]]) -> int | None:
    """Índice del módulo actual: primer módulo desbloqueado e incompleto.

    ``progress_pairs`` = (total_topics, completed_topics) por módulo, en orden.
    Devuelve None si todos los módulos están completos (curso terminado).
    """
    locks = compute_locks(progress_pairs)
    for i, ((total, done), locked) in enumerate(zip(progress_pairs, locks)):
        if not locked and (total == 0 or done < total):
            return i
    return None


def build_diagnostic(stats: list[TopicStat], module_id: int) -> ModuleDiagnostic:
    """Clasifica los temas del módulo actual y decide el siguiente paso. Pura."""
    ordered = sorted(stats, key=lambda s: s.order_index)
    weak: list[TopicDiagnostic] = []
    practice: list[TopicDiagnostic] = []
    pending: list[TopicStat] = []
    coding_pending: list[TopicStat] = []

    for s in ordered:
        if not s.visited:
            pending.append(s)
        if s.has_coding_pending:
            coding_pending.append(s)
        if s.best_score is None:
            continue
        # Dominado (≥80) tiene precedencia sobre la regla de intentos fallidos.
        if s.best_score < WEAK_SCORE or (
            s.failed_attempts >= WEAK_FAILED_ATTEMPTS and s.best_score < PRACTICE_SCORE
        ):
            weak.append(TopicDiagnostic(
                topic_id=s.topic_id, title=s.title,
                best_score=s.best_score, attempts=s.attempts,
            ))
        elif s.best_score < PRACTICE_SCORE:
            practice.append(TopicDiagnostic(
                topic_id=s.topic_id, title=s.title,
                best_score=s.best_score, attempts=s.attempts,
            ))

    if weak:
        next_action = NextAction(
            kind="retry_quiz",
            label=f"Repasar «{weak[0].title}»",
            route=f"/topics/{weak[0].topic_id}",
        )
    elif pending:
        next_action = NextAction(
            kind="next_topic",
            label=f"Continuar con «{pending[0].title}»",
            route=f"/topics/{pending[0].topic_id}",
        )
    elif coding_pending:
        next_action = NextAction(
            kind="coding_challenge",
            label=f"Resolver el desafío de «{coding_pending[0].title}»",
            route=f"/topics/{coding_pending[0].topic_id}",
        )
    else:
        next_action = NextAction(
            kind="module", label="Ver el módulo", route=f"/modules/{module_id}",
        )

    return ModuleDiagnostic(weak=weak, practice=practice, next_action=next_action)
```

- [ ] **Step 4: Verificar que pasan**

Run: `cd C:\tutor-ia-rfa\backend; python -m pytest tests/unit/test_companion_service.py -v`
Expected: 13 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/companion_service.py backend/tests/unit/test_companion_service.py
git commit -m "feat(companion): motor puro de posicion actual y diagnostico por modulo"
```

---

### Task 3: `build_greeting` (TDD)

**Files:**
- Modify: `backend/app/services/companion_service.py`
- Test: `backend/tests/unit/test_companion_service.py`

- [ ] **Step 1: Agregar tests que fallan**

Añadir al final de `backend/tests/unit/test_companion_service.py`:

```python
# --- build_greeting: plantillas por estado ---
from app.services.companion_service import build_greeting


def _pos(**over):
    base = dict(
        module_id=3, module_title="Interfaces de Usuario", icon_name=None,
        color_hex=None, progress_pct=60.0, topics_done=3, topics_total=5,
        course_completed=False,
    )
    base.update(over)
    return CompanionPosition(**base)


def test_greeting_course_completed():
    g = build_greeting(_pos(course_completed=True), build_diagnostic([], module_id=3))
    assert "Felicitaciones" in g


def test_greeting_mentions_weak_topic():
    d = build_diagnostic(
        [_stat(title="Layouts", best_score=45, failed_attempts=2)], module_id=3
    )
    g = build_greeting(_pos(), d)
    assert "Layouts" in g and "Interfaces de Usuario" in g


def test_greeting_fresh_module():
    d = build_diagnostic([_stat(visited=False)], module_id=3)
    g = build_greeting(_pos(topics_done=0, progress_pct=0.0), d)
    assert "comenzando" in g.lower()


def test_greeting_default_mentions_next_step():
    d = build_diagnostic([_stat(best_score=85, completed=True)], module_id=3)
    g = build_greeting(_pos(), d)
    assert "siguiente paso" in g.lower()
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `cd C:\tutor-ia-rfa\backend; python -m pytest tests/unit/test_companion_service.py -v`
Expected: 4 FAIL con `ImportError: cannot import name 'build_greeting'` (los 13 previos PASS)

- [ ] **Step 3: Implementar `build_greeting`**

Añadir a `backend/app/services/companion_service.py` (después de `build_diagnostic`):

```python
NEEDS_ASSESSMENT_GREETING = (
    "Antes de empezar, realiza tu evaluación de entrada para personalizar "
    "tu ruta de aprendizaje."
)
EMPTY_COURSE_GREETING = "Aún no hay módulos disponibles. Vuelve pronto."


def build_greeting(position: CompanionPosition, diagnostic: ModuleDiagnostic) -> str:
    """Saludo contextual del tutor por plantillas (español peruano). Pura."""
    if position.course_completed:
        return (
            "¡Felicitaciones! Completaste todos los módulos del curso. "
            "Puedes repasar libremente cualquier tema o desafío."
        )
    pct = round(position.progress_pct)
    if diagnostic.weak:
        return (
            f"Estás en «{position.module_title}» — {pct}% completado. "
            f"Veo que te cuesta «{diagnostic.weak[0].title}», ¿lo repasamos?"
        )
    if position.topics_done == 0:
        return (
            f"Estás comenzando «{position.module_title}». "
            "Te acompaño paso a paso; empieza con el primer tema."
        )
    return (
        f"Estás en «{position.module_title}» — {pct}% completado. "
        f"Tu siguiente paso: {diagnostic.next_action.label}."
    )
```

- [ ] **Step 4: Verificar que pasan**

Run: `cd C:\tutor-ia-rfa\backend; python -m pytest tests/unit/test_companion_service.py -v`
Expected: 17 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/companion_service.py backend/tests/unit/test_companion_service.py
git commit -m "feat(companion): saludo contextual por plantillas segun estado del estudiante"
```

---

### Task 4: `gather_companion` — resolver estado desde BD

**Files:**
- Modify: `backend/app/services/companion_service.py`

Glue de BD (se valida vía integration tests de Task 5; mismo trato que `gather_snapshot` en Fase 1).

- [ ] **Step 1: Agregar imports de BD al inicio del archivo**

Reemplazar el bloque de imports de `backend/app/services/companion_service.py` por:

```python
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coding import CodingChallenge, CodingSubmission
from app.models.learning_resource import LearningResource
from app.models.module import Module
from app.models.progress import UserTopicProgress
from app.models.quiz import QuizAttempt
from app.models.topic import Topic
from app.models.user_level import UserLevel
from app.schemas.companion import (
    CompanionPosition,
    CompanionResponse,
    ModuleDiagnostic,
    NextAction,
    TopicDiagnostic,
    TopicStat,
)
from app.schemas.learning_resource import LearningResourceResponse
from app.services.module_service import compute_locks
```

- [ ] **Step 2: Agregar el gather al final del archivo**

```python
async def _gather_topic_stats(user, module_id: int, db: AsyncSession) -> list[TopicStat]:
    """Stats por tema del módulo actual: quiz, progreso y coding pendiente."""
    topics = (
        await db.execute(
            select(Topic.id, Topic.title, Topic.order_index)
            .where(Topic.module_id == module_id, Topic.is_active == True)  # noqa: E712
            .order_by(Topic.order_index)
        )
    ).all()
    topic_ids = [t[0] for t in topics]
    if not topic_ids:
        return []

    prog_rows = (
        await db.execute(
            select(UserTopicProgress.topic_id, UserTopicProgress.is_completed).where(
                UserTopicProgress.user_id == user.id,
                UserTopicProgress.topic_id.in_(topic_ids),
            )
        )
    ).all()
    progress = {tid: completed for tid, completed in prog_rows}

    quiz_rows = (
        await db.execute(
            select(
                QuizAttempt.topic_id,
                func.max(QuizAttempt.score).label("best"),
                func.count(QuizAttempt.id).label("attempts"),
                func.count(QuizAttempt.id)
                .filter(QuizAttempt.is_passed == False)  # noqa: E712
                .label("failed"),
            )
            .where(QuizAttempt.user_id == user.id, QuizAttempt.topic_id.in_(topic_ids))
            .group_by(QuizAttempt.topic_id)
        )
    ).all()
    quiz = {row[0]: row for row in quiz_rows}

    # Desafíos de catálogo (no AI per-usuario) y cuáles ya aprobó (≥60)
    chal_rows = (
        await db.execute(
            select(CodingChallenge.topic_id, CodingChallenge.id).where(
                CodingChallenge.topic_id.in_(topic_ids),
                CodingChallenge.is_ai_generated == False,  # noqa: E712
            )
        )
    ).all()
    challenge_topics: dict[int, list[int]] = {}
    for tid, cid in chal_rows:
        challenge_topics.setdefault(tid, []).append(cid)
    all_challenge_ids = [cid for ids in challenge_topics.values() for cid in ids]

    passed_challenge_ids: set[int] = set()
    if all_challenge_ids:
        sub_rows = (
            await db.execute(
                select(CodingSubmission.challenge_id).where(
                    CodingSubmission.user_id == user.id,
                    CodingSubmission.challenge_id.in_(all_challenge_ids),
                    CodingSubmission.score >= CODING_PASS_SCORE,
                )
            )
        ).all()
        passed_challenge_ids = {r[0] for r in sub_rows}

    stats: list[TopicStat] = []
    for tid, title, order_index in topics:
        q = quiz.get(tid)
        cids = challenge_topics.get(tid, [])
        stats.append(TopicStat(
            topic_id=tid,
            title=title,
            order_index=order_index,
            visited=tid in progress,
            completed=bool(progress.get(tid)),
            best_score=float(q[1]) if q else None,
            attempts=int(q[2]) if q else 0,
            failed_attempts=int(q[3]) if q else 0,
            has_coding_pending=any(c not in passed_challenge_ids for c in cids),
        ))
    return stats


async def gather_companion(user, db: AsyncSession) -> CompanionResponse:
    """Resuelve posición + diagnóstico + recursos desde BD (sin LLM)."""
    # 0. Sin evaluación de entrada → respuesta mínima (consistente con regla R1)
    level_row = await db.execute(select(UserLevel).where(UserLevel.user_id == user.id))
    if level_row.scalar_one_or_none() is None:
        return CompanionResponse(
            needs_assessment=True, position=None, diagnostic=None,
            resources=[], greeting=NEEDS_ASSESSMENT_GREETING,
        )

    # 1. Módulos + progreso (mismas 3 consultas planas que module_service)
    mods_res = await db.execute(
        select(Module).where(Module.is_active == True).order_by(Module.order_index)  # noqa: E712
    )
    modules = list(mods_res.scalars().all())
    if not modules:
        return CompanionResponse(
            needs_assessment=False, position=None, diagnostic=None,
            resources=[], greeting=EMPTY_COURSE_GREETING,
        )

    totals_rows = (
        await db.execute(
            select(Topic.module_id, func.count(Topic.id))
            .where(Topic.is_active == True)  # noqa: E712
            .group_by(Topic.module_id)
        )
    ).all()
    totals = {module_id: count for module_id, count in totals_rows}

    done_rows = (
        await db.execute(
            select(Topic.module_id, func.count(UserTopicProgress.id))
            .join(UserTopicProgress, UserTopicProgress.topic_id == Topic.id)
            .where(
                UserTopicProgress.user_id == user.id,
                UserTopicProgress.is_completed == True,  # noqa: E712
                Topic.is_active == True,  # noqa: E712
            )
            .group_by(Topic.module_id)
        )
    ).all()
    done = {module_id: count for module_id, count in done_rows}

    pairs = [(totals.get(m.id, 0), done.get(m.id, 0)) for m in modules]
    idx = pick_current_index(pairs)
    course_completed = idx is None
    current = modules[-1] if course_completed else modules[idx]
    total, completed = pairs[-1] if course_completed else pairs[idx]

    position = CompanionPosition(
        module_id=current.id,
        module_title=current.title,
        icon_name=current.icon_name,
        color_hex=current.color_hex,
        progress_pct=round(completed / total * 100, 1) if total else 0.0,
        topics_done=completed,
        topics_total=total,
        course_completed=course_completed,
    )

    # 2. Diagnóstico del módulo actual
    stats = await _gather_topic_stats(user, current.id, db)
    diagnostic = build_diagnostic(stats, current.id)

    # 3. Recursos curados del módulo actual (máx 3)
    res_rows = await db.execute(
        select(LearningResource)
        .where(
            LearningResource.is_active == True,  # noqa: E712
            LearningResource.module_id == current.id,
        )
        .order_by(LearningResource.order_index, LearningResource.id)
        .limit(MAX_RESOURCES)
    )
    resources = [
        LearningResourceResponse.model_validate(r) for r in res_rows.scalars().all()
    ]

    return CompanionResponse(
        needs_assessment=False,
        position=position,
        greeting=build_greeting(position, diagnostic),
        diagnostic=diagnostic,
        resources=resources,
    )
```

- [ ] **Step 3: Verificar que la suite unit sigue verde y el módulo importa**

Run: `cd C:\tutor-ia-rfa\backend; python -m pytest tests/unit/test_companion_service.py -v; python -c "from app.services.companion_service import gather_companion; print('ok')"`
Expected: 17 PASS + `ok`

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/companion_service.py
git commit -m "feat(companion): gather de posicion, stats por tema y recursos desde BD"
```

---

### Task 5: Endpoint `GET /tutor/companion` + integration tests (TDD)

**Files:**
- Modify: `backend/app/routers/tutor.py`
- Test: `backend/tests/integration/test_router_companion.py`

- [ ] **Step 1: Escribir integration tests que fallan**

Crear `backend/tests/integration/test_router_companion.py`:

```python
"""Integration tests para /api/v1/tutor/companion."""
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.companion import (
    CompanionPosition,
    CompanionResponse,
    ModuleDiagnostic,
    NextAction,
    TopicDiagnostic,
)
from tests.integration.conftest import result_scalar_one_or_none


def _payload() -> CompanionResponse:
    return CompanionResponse(
        needs_assessment=False,
        position=CompanionPosition(
            module_id=3, module_title="Interfaces de Usuario", icon_name=None,
            color_hex="#3b82f6", progress_pct=60.0, topics_done=3, topics_total=5,
            course_completed=False,
        ),
        greeting="Estás en «Interfaces de Usuario» — 60% completado.",
        diagnostic=ModuleDiagnostic(
            weak=[TopicDiagnostic(topic_id=12, title="Layouts", best_score=45.0, attempts=2)],
            practice=[],
            next_action=NextAction(
                kind="retry_quiz", label="Repasar «Layouts»", route="/topics/12"
            ),
        ),
        resources=[],
    )


@pytest.mark.asyncio
async def test_companion_returns_payload(client):
    with patch(
        "app.routers.tutor.gather_companion", new=AsyncMock(return_value=_payload())
    ):
        r = await client.get("/api/v1/tutor/companion")
    assert r.status_code == 200
    body = r.json()
    assert body["needs_assessment"] is False
    assert body["position"]["module_id"] == 3
    assert body["diagnostic"]["weak"][0]["title"] == "Layouts"
    assert body["diagnostic"]["next_action"]["route"] == "/topics/12"


@pytest.mark.asyncio
async def test_companion_needs_assessment_via_real_gather(client, mock_db):
    # Sin patch: gather_companion real corta en la 1.ª query (UserLevel → None).
    mock_db.execute.side_effect = [result_scalar_one_or_none(None)]
    r = await client.get("/api/v1/tutor/companion")
    assert r.status_code == 200
    body = r.json()
    assert body["needs_assessment"] is True
    assert body["position"] is None
    assert body["diagnostic"] is None
    assert "evaluación de entrada" in body["greeting"]


@pytest.mark.asyncio
async def test_companion_served_from_cache_skips_service(client, mock_redis_pipe):
    cached = _payload().model_dump(mode="json")
    mock_redis_pipe.get = AsyncMock(return_value=json.dumps(cached))
    with patch("app.routers.tutor.gather_companion", new=AsyncMock()) as svc:
        r = await client.get("/api/v1/tutor/companion")
    assert r.status_code == 200
    svc.assert_not_called()


@pytest.mark.asyncio
async def test_companion_requires_auth(anon_client):
    r = await anon_client.get("/api/v1/tutor/companion")
    assert r.status_code in (401, 403)  # dep real de auth sin token
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `cd C:\tutor-ia-rfa\backend; python -m pytest tests/integration/test_router_companion.py -v`
Expected: FAIL — 404 en las llamadas (ruta no existe) y `AttributeError` en los patch de `app.routers.tutor.gather_companion`

- [ ] **Step 3: Agregar el endpoint al router**

En `backend/app/routers/tutor.py`:

Reemplazar:
```python
from app.schemas.tutor import NudgeResponse
from app.services.tutor_service import get_nudges
```
por:
```python
from app.schemas.companion import CompanionResponse
from app.schemas.tutor import NudgeResponse
from app.services.companion_service import gather_companion
from app.services.tutor_service import get_nudges
```

Y reemplazar:
```python
_NO_CACHE = {"quiz_result", "coding_result", "assessment_result"}
NUDGE_CACHE_TTL = 30  # seconds
```
por:
```python
_NO_CACHE = {"quiz_result", "coding_result", "assessment_result"}
NUDGE_CACHE_TTL = 30  # seconds
COMPANION_CACHE_TTL = 60  # seconds
```

Añadir al final del archivo:

```python
@router.get("/companion", response_model=CompanionResponse)
async def get_tutor_companion(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """Posición del estudiante + diagnóstico del módulo actual (Fase 5, sin LLM)."""

    async def _build() -> dict:
        payload = await gather_companion(current_user, db)
        return payload.model_dump(mode="json")

    data = await cached_json(
        redis_client,
        f"companion:{current_user.id}",
        ttl=COMPANION_CACHE_TTL,
        loader=_build,
    )
    return CompanionResponse.model_validate(data)
```

- [ ] **Step 4: Verificar que pasan**

Run: `cd C:\tutor-ia-rfa\backend; python -m pytest tests/integration/test_router_companion.py -v`
Expected: 4 PASS

- [ ] **Step 5: Correr toda la suite backend (no romper nada, incluido el guardián ISO)**

Run: `cd C:\tutor-ia-rfa\backend; python -m pytest tests/ -q`
Expected: todo verde (396 previos + 21 nuevos), 0 fallos

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/tutor.py backend/tests/integration/test_router_companion.py
git commit -m "feat(companion): endpoint GET /tutor/companion con cache Redis TTL 60s"
```

---

### Task 6: Frontend — types + api + hook

**Files:**
- Create: `frontend/src/types/companion.ts`
- Create: `frontend/src/hooks/useCompanion.ts`
- Modify: `frontend/src/api/tutor.ts`

- [ ] **Step 1: Crear `frontend/src/types/companion.ts`**

```ts
import type { LearningResource } from './resource'

export interface CompanionPosition {
  module_id: number
  module_title: string
  icon_name: string | null
  color_hex: string | null
  progress_pct: number
  topics_done: number
  topics_total: number
  course_completed: boolean
}

export interface TopicDiagnostic {
  topic_id: number
  title: string
  best_score: number | null
  attempts: number
}

export type NextActionKind = 'retry_quiz' | 'next_topic' | 'coding_challenge' | 'module'

export interface NextAction {
  kind: NextActionKind
  label: string
  route: string
}

export interface ModuleDiagnostic {
  weak: TopicDiagnostic[]
  practice: TopicDiagnostic[]
  next_action: NextAction
}

export interface CompanionResponse {
  needs_assessment: boolean
  position: CompanionPosition | null
  greeting: string
  diagnostic: ModuleDiagnostic | null
  resources: LearningResource[]
}
```

- [ ] **Step 2: Extender `frontend/src/api/tutor.ts`**

Reemplazar el archivo completo por:

```ts
import apiClient from './client'
import type { NudgeResponse, NudgeContext } from '@/types/tutor'
import type { CompanionResponse } from '@/types/companion'

export interface NudgeParams {
  context: NudgeContext
  topicId?: number
  moduleId?: number
  score?: number
}

export const tutorApi = {
  getNudges: (p: NudgeParams) =>
    apiClient.get<NudgeResponse>('/tutor/nudges', {
      params: {
        context: p.context,
        topic_id: p.topicId,
        module_id: p.moduleId,
        score: p.score,
      },
    }),
  getCompanion: () => apiClient.get<CompanionResponse>('/tutor/companion'),
}
```

- [ ] **Step 3: Crear `frontend/src/hooks/useCompanion.ts`**

```ts
import { useQuery } from '@tanstack/react-query'
import { tutorApi } from '@/api/tutor'

export function useCompanion() {
  return useQuery({
    queryKey: ['tutor-companion'],
    queryFn: async () => {
      const { data } = await tutorApi.getCompanion()
      return data
    },
    staleTime: 60_000,
  })
}
```

- [ ] **Step 4: Verificar tipos**

Run: `cd C:\tutor-ia-rfa\frontend; npx tsc --noEmit`
Expected: sin errores

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/companion.ts frontend/src/api/tutor.ts frontend/src/hooks/useCompanion.ts
git commit -m "feat(companion): types, api y hook useCompanion en frontend"
```

---

### Task 7: `DiagnosticChips` (TDD)

**Files:**
- Create: `frontend/src/components/tutor/DiagnosticChips.tsx`
- Test: `frontend/src/components/tutor/DiagnosticChips.test.tsx`

- [ ] **Step 1: Escribir test que falla**

Crear `frontend/src/components/tutor/DiagnosticChips.test.tsx`:

```tsx
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import DiagnosticChips from './DiagnosticChips'
import type { ModuleDiagnostic } from '@/types/companion'

function makeDiagnostic(over: Partial<ModuleDiagnostic> = {}): ModuleDiagnostic {
  return {
    weak: [{ topic_id: 12, title: 'Layouts', best_score: 45, attempts: 2 }],
    practice: [{ topic_id: 13, title: 'Intents', best_score: 70, attempts: 1 }],
    next_action: { kind: 'retry_quiz', label: 'Repasar «Layouts»', route: '/topics/12' },
    ...over,
  }
}

describe('<DiagnosticChips />', () => {
  it('renders weak and practice chips linking to topics', () => {
    render(
      <MemoryRouter>
        <DiagnosticChips diagnostic={makeDiagnostic()} />
      </MemoryRouter>
    )
    const weak = screen.getByRole('link', { name: /Repasar: Layouts/ })
    expect(weak).toHaveAttribute('href', '/topics/12')
    const practice = screen.getByRole('link', { name: /Afianzar: Intents/ })
    expect(practice).toHaveAttribute('href', '/topics/13')
  })

  it('renders nothing when there is no diagnostic content', () => {
    const { container } = render(
      <MemoryRouter>
        <DiagnosticChips diagnostic={makeDiagnostic({ weak: [], practice: [] })} />
      </MemoryRouter>
    )
    expect(container).toBeEmptyDOMElement()
  })
})
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `cd C:\tutor-ia-rfa\frontend; npx vitest run src/components/tutor/DiagnosticChips.test.tsx`
Expected: FAIL — `Failed to resolve import "./DiagnosticChips"`

- [ ] **Step 3: Implementar el componente**

Crear `frontend/src/components/tutor/DiagnosticChips.tsx`:

```tsx
import { Link } from 'react-router-dom'
import { Repeat, Target } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ModuleDiagnostic } from '@/types/companion'

interface Props {
  diagnostic: ModuleDiagnostic
  className?: string
}

const CHIP_BASE =
  'inline-flex items-center gap-1.5 min-h-[44px] px-3.5 rounded-full border text-sm font-medium ' +
  'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'

export default function DiagnosticChips({ diagnostic, className }: Props) {
  const { weak, practice } = diagnostic
  if (weak.length === 0 && practice.length === 0) return null
  return (
    <ul aria-label="Diagnóstico de temas del módulo" className={cn('flex flex-wrap gap-2', className)}>
      {weak.map((t) => (
        <li key={`weak-${t.topic_id}`}>
          <Link
            to={`/topics/${t.topic_id}`}
            className={cn(CHIP_BASE, 'bg-warning/10 text-warning border-warning/30 hover:bg-warning/20')}
          >
            <Repeat className="w-3.5 h-3.5" aria-hidden="true" />
            Repasar: {t.title}
          </Link>
        </li>
      ))}
      {practice.map((t) => (
        <li key={`practice-${t.topic_id}`}>
          <Link
            to={`/topics/${t.topic_id}`}
            className={cn(CHIP_BASE, 'bg-primary/10 text-primary border-primary/30 hover:bg-primary/20')}
          >
            <Target className="w-3.5 h-3.5" aria-hidden="true" />
            Afianzar: {t.title}
          </Link>
        </li>
      ))}
    </ul>
  )
}
```

- [ ] **Step 4: Verificar que pasa**

Run: `cd C:\tutor-ia-rfa\frontend; npx vitest run src/components/tutor/DiagnosticChips.test.tsx`
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/tutor/DiagnosticChips.tsx frontend/src/components/tutor/DiagnosticChips.test.tsx
git commit -m "feat(companion): chips de diagnostico repasar/afianzar"
```

---

### Task 8: `CompanionPanel` + integración en Dashboard (TDD)

**Files:**
- Create: `frontend/src/components/tutor/CompanionPanel.tsx`
- Test: `frontend/src/components/tutor/CompanionPanel.test.tsx`
- Modify: `frontend/src/pages/DashboardPage.tsx`

- [ ] **Step 1: Escribir test que falla**

Crear `frontend/src/components/tutor/CompanionPanel.test.tsx`:

```tsx
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import CompanionPanel from './CompanionPanel'
import type { CompanionResponse } from '@/types/companion'

function makeData(over: Partial<CompanionResponse> = {}): CompanionResponse {
  return {
    needs_assessment: false,
    position: {
      module_id: 3, module_title: 'Interfaces de Usuario', icon_name: null,
      color_hex: '#3b82f6', progress_pct: 60, topics_done: 3, topics_total: 5,
      course_completed: false,
    },
    greeting: 'Estás en «Interfaces de Usuario» — 60% completado.',
    diagnostic: {
      weak: [{ topic_id: 12, title: 'Layouts', best_score: 45, attempts: 2 }],
      practice: [{ topic_id: 13, title: 'Intents', best_score: 70, attempts: 1 }],
      next_action: { kind: 'retry_quiz', label: 'Repasar «Layouts»', route: '/topics/12' },
    },
    resources: [
      {
        id: 1, module_id: 3, topic_id: null, kind: 'video',
        title: 'Curso de Layouts', url: 'https://example.com', author: null,
        description: null, order_index: 0, is_active: true,
      },
    ],
    ...over,
  }
}

function renderPanel(data = makeData()) {
  return render(
    <MemoryRouter>
      <CompanionPanel data={data} />
    </MemoryRouter>
  )
}

describe('<CompanionPanel />', () => {
  it('renders current module, greeting and progress', () => {
    renderPanel()
    expect(screen.getByText('Interfaces de Usuario')).toBeInTheDocument()
    expect(screen.getByText(/60% completado/)).toBeInTheDocument()
    expect(screen.getByText(/3 de 5 temas/)).toBeInTheDocument()
  })

  it('renders next action CTA', () => {
    renderPanel()
    expect(screen.getByRole('button', { name: /Repasar «Layouts»/ })).toBeInTheDocument()
  })

  it('renders diagnostic chips and module resources', () => {
    renderPanel()
    expect(screen.getByRole('link', { name: /Repasar: Layouts/ })).toBeInTheDocument()
    expect(screen.getByText('Curso de Layouts')).toBeInTheDocument()
  })

  it('renders nothing without position or diagnostic', () => {
    const { container } = renderPanel(makeData({ position: null, diagnostic: null }))
    expect(container).toBeEmptyDOMElement()
  })
})
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `cd C:\tutor-ia-rfa\frontend; npx vitest run src/components/tutor/CompanionPanel.test.tsx`
Expected: FAIL — `Failed to resolve import "./CompanionPanel"`

- [ ] **Step 3: Implementar el componente**

Crear `frontend/src/components/tutor/CompanionPanel.tsx`:

```tsx
import { useNavigate } from 'react-router-dom'
import { ArrowRight, BookOpen, MapPin } from 'lucide-react'
import { Button } from '@/components/ui/button'
import DiagnosticChips from './DiagnosticChips'
import ResourceCard from '@/components/resources/ResourceCard'
import type { CompanionResponse } from '@/types/companion'

/**
 * Panel «Tu ruta» (Fase 5): posición del estudiante, diagnóstico del módulo
 * actual y recursos curados. Reemplaza al hero del Dashboard cuando el
 * endpoint /tutor/companion responde; si no, el hero clásico queda como
 * fallback (degradación silenciosa).
 */
export default function CompanionPanel({ data }: { data: CompanionResponse }) {
  const navigate = useNavigate()
  const { position, diagnostic, greeting, resources } = data
  if (!position || !diagnostic) return null
  const pct = Math.round(position.progress_pct)

  return (
    <>
      <section
        aria-labelledby="companion-heading"
        className="relative bg-brand-hero text-white rounded-2xl p-6 sm:p-7 mb-6 shadow-brand-lg overflow-hidden"
      >
        <div className="absolute -top-16 -right-16 w-56 h-56 rounded-full bg-heritage-500/15 blur-3xl" aria-hidden="true" />
        <div className="absolute bottom-0 left-0 h-1 w-full bg-heritage-accent" aria-hidden="true" />
        <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-xs text-primary-200 mb-1 flex items-center gap-1 uppercase tracking-wider font-semibold">
              <MapPin className="w-4 h-4" aria-hidden="true" />
              {position.course_completed ? 'Curso completado' : 'Tu módulo actual'}
            </p>
            <h2 id="companion-heading" className="font-extrabold text-lg sm:text-xl break-words line-clamp-2">
              {position.module_title}
            </h2>
            <p className="text-sm text-primary-100 mt-1 break-words">{greeting}</p>
            <div className="mt-3 max-w-xs">
              <div className="h-1.5 w-full rounded-full bg-white/20 overflow-hidden">
                <div className="h-full bg-heritage-accent transition-all" style={{ width: `${pct}%` }} />
              </div>
              <p className="text-xs text-primary-200 mt-1">
                {position.topics_done} de {position.topics_total} temas · {pct}%
              </p>
            </div>
          </div>
          <Button
            variant="secondary"
            size="lg"
            className="bg-white text-institutional-700 hover:bg-heritage-50 dark:bg-white dark:text-institutional-700 dark:hover:bg-heritage-50 shadow-brand-md w-full sm:w-auto shrink-0"
            onClick={() => navigate(diagnostic.next_action.route)}
          >
            {diagnostic.next_action.label}
            <ArrowRight className="w-4 h-4 ml-2" aria-hidden="true" />
          </Button>
        </div>
      </section>

      <DiagnosticChips diagnostic={diagnostic} className="mb-6" />

      {resources.length > 0 && (
        <section aria-label="Recursos de tu módulo actual" className="space-y-2 mb-8">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <BookOpen className="h-4 w-4 text-primary" aria-hidden="true" />
            Recursos de tu módulo actual
          </h2>
          <div className="grid gap-2 sm:grid-cols-2">
            {resources.map((r) => (
              <ResourceCard key={r.id} resource={r} />
            ))}
          </div>
        </section>
      )}
    </>
  )
}
```

- [ ] **Step 4: Verificar que pasa**

Run: `cd C:\tutor-ia-rfa\frontend; npx vitest run src/components/tutor/CompanionPanel.test.tsx`
Expected: 4 PASS

- [ ] **Step 5: Integrar en `DashboardPage.tsx`**

En `frontend/src/pages/DashboardPage.tsx`:

a) Añadir imports (junto a los existentes de tutor/resources):

```tsx
import CompanionPanel from '@/components/tutor/CompanionPanel'
import { useCompanion } from '@/hooks/useCompanion'
```

b) Después del query de `streak` (tras el bloque `const { data: streak, ... })`), añadir:

```tsx
  const { data: companion } = useCompanion()
  const showCompanion =
    !!companion && !companion.needs_assessment && !!companion.position && !!companion.diagnostic
```

c) Reemplazar el bloque del hero — desde el comentario `{/* Hero: the single next step on the path (always present) */}` hasta el `</section>` que lo cierra — por el mismo bloque envuelto en condicional:

```tsx
      {/* Hero: companion «Tu ruta» (Fase 5); hero clásico como fallback */}
      {showCompanion ? (
        <CompanionPanel data={companion} />
      ) : (
        <section
          aria-labelledby="hero-resume"
          className="relative bg-brand-hero text-white rounded-2xl p-6 sm:p-7 mb-6 shadow-brand-lg overflow-hidden"
        >
          {/* ... contenido EXACTO del hero existente, sin cambios ... */}
        </section>
      )}
```

(El contenido interno del `<section>` no se modifica; solo se envuelve en el ternario.)

d) Reemplazar el mount inferior de recursos:

```tsx
      {/* Resources for first recommended module */}
      {data?.recommended_modules?.[0] && (
        <ResourceList moduleId={data.recommended_modules[0].id} title="Recursos recomendados" />
      )}
```

por (evita duplicar recursos cuando el panel ya los muestra):

```tsx
      {/* Resources fallback: solo cuando el companion no está visible */}
      {!showCompanion && data?.recommended_modules?.[0] && (
        <ResourceList moduleId={data.recommended_modules[0].id} title="Recursos recomendados" />
      )}
```

- [ ] **Step 6: Verificar tipos + suite frontend**

Run: `cd C:\tutor-ia-rfa\frontend; npx tsc --noEmit; npx vitest run`
Expected: sin errores de tipos; todos los tests PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/tutor/CompanionPanel.tsx frontend/src/components/tutor/CompanionPanel.test.tsx frontend/src/pages/DashboardPage.tsx
git commit -m "feat(companion): panel Tu ruta en Dashboard con fallback al hero clasico"
```

---

### Task 9: Burbuja preview en `FloatingTutor` (TDD)

**Files:**
- Modify: `frontend/src/components/tutor/FloatingTutor.tsx`
- Modify: `frontend/src/components/tutor/FloatingTutor.test.tsx`

⚠ `FloatingTutor` pasará a importar `useCompanion`; su test existente DEBE mockear el hook a nivel de archivo o `useQuery` explotará sin `QueryClientProvider`.

- [ ] **Step 1: Leer `FloatingTutor.test.tsx` existente y agregar mock + tests que fallan**

Al inicio del archivo de test (junto a los mocks existentes de hooks de chat), añadir:

```tsx
let companionData: import('@/types/companion').CompanionResponse | undefined

vi.mock('@/hooks/useCompanion', () => ({
  useCompanion: () => ({ data: companionData }),
}))
```

(Default `undefined` → los tests existentes no muestran burbuja y siguen verdes.)

Añadir un nuevo `describe` al final:

```tsx
describe('FloatingTutor greeting bubble', () => {
  beforeEach(() => {
    sessionStorage.clear()
    companionData = {
      needs_assessment: false,
      position: null,
      greeting: 'Estás en «Interfaces de Usuario» — 60% completado.',
      diagnostic: null,
      resources: [],
    }
  })

  afterEach(() => {
    companionData = undefined
  })

  it('shows the greeting bubble once per session', () => {
    const { unmount } = renderTutor()
    expect(screen.getByRole('status')).toHaveTextContent('Interfaces de Usuario')
    unmount()
    renderTutor()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('close button hides the bubble', async () => {
    renderTutor()
    await userEvent.click(screen.getByRole('button', { name: 'Cerrar saludo del tutor' }))
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
```

Notas para el ejecutor: usar el helper de render que ya exista en el archivo (`renderTutor()` o equivalente — si se llama distinto, adaptar el nombre, NO duplicar wrappers). Si el archivo no usa `userEvent`, importar de `@testing-library/user-event`; `vi`, `beforeEach`, `afterEach` desde `vitest`.

- [ ] **Step 2: Correr y verificar que fallan**

Run: `cd C:\tutor-ia-rfa\frontend; npx vitest run src/components/tutor/FloatingTutor.test.tsx`
Expected: los 2 tests nuevos FAIL (no existe burbuja); los existentes PASS

- [ ] **Step 3: Implementar la burbuja**

En `frontend/src/components/tutor/FloatingTutor.tsx`:

a) Añadir import:

```tsx
import { useCompanion } from '@/hooks/useCompanion'
```

b) Antes de `export default function FloatingTutor()`, añadir:

```tsx
const GREETING_SESSION_KEY = 'tutor_greeting_shown'
const GREETING_AUTOHIDE_MS = 12_000
```

c) Dentro del componente, después de `const sendMessage = useSendMessage(sessionId)`, añadir:

```tsx
  const [showGreeting, setShowGreeting] = useState(false)
  const { data: companion } = useCompanion()

  // Burbuja preview (Fase 5): saludo contextual, 1 vez por sesión de navegador.
  useEffect(() => {
    if (open || !companion?.greeting) return
    if (sessionStorage.getItem(GREETING_SESSION_KEY)) return
    sessionStorage.setItem(GREETING_SESSION_KEY, '1')
    setShowGreeting(true)
    const timer = setTimeout(() => setShowGreeting(false), GREETING_AUTOHIDE_MS)
    return () => clearTimeout(timer)
  }, [companion?.greeting, open])

  useEffect(() => {
    if (!showGreeting) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setShowGreeting(false)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [showGreeting])
```

d) En `handleOpen`, como primera línea del cuerpo, añadir:

```tsx
    setShowGreeting(false)
```

e) Reemplazar el bloque `{!open && ( <button ...> ... </button> )}` por:

```tsx
      {!open && (
        <>
          {showGreeting && companion?.greeting && (
            <div
              role="status"
              className="fixed bottom-20 right-4 z-40 max-w-[280px] rounded-xl border border-border
                         bg-card p-3 shadow-xl
                         motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2"
            >
              <p className="text-sm text-foreground">{companion.greeting}</p>
              <div className="mt-2 flex items-center gap-2">
                <Button size="sm" onClick={handleOpen}>
                  Abrir tutor
                </Button>
                <button
                  type="button"
                  onClick={() => setShowGreeting(false)}
                  aria-label="Cerrar saludo del tutor"
                  className="inline-flex items-center justify-center min-h-[44px] min-w-[44px]
                             rounded-lg text-muted-foreground hover:text-foreground transition-colors
                             focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
          <button
            type="button"
            onClick={handleOpen}
            aria-label="Abrir tutor IA"
            className="fixed bottom-4 right-4 z-40 inline-flex items-center justify-center
                       h-14 w-14 rounded-full bg-primary text-primary-foreground shadow-lg
                       hover:bg-primary/90 transition-colors
                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Sparkles className="h-6 w-6" aria-hidden="true" />
          </button>
        </>
      )}
```

(El `<button>` flotante queda EXACTAMENTE igual; solo se envuelve en fragment junto a la burbuja.)

- [ ] **Step 4: Verificar que pasan**

Run: `cd C:\tutor-ia-rfa\frontend; npx vitest run src/components/tutor/FloatingTutor.test.tsx`
Expected: todos PASS (existentes + 2 nuevos)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/tutor/FloatingTutor.tsx frontend/src/components/tutor/FloatingTutor.test.tsx
git commit -m "feat(companion): burbuja preview del tutor con saludo contextual 1x por sesion"
```

---

### Task 10: Franja de diagnóstico en `ModuleDetailPage`

**Files:**
- Modify: `frontend/src/pages/ModuleDetailPage.tsx`

- [ ] **Step 1: Añadir imports y hook**

En `frontend/src/pages/ModuleDetailPage.tsx`, añadir imports:

```tsx
import DiagnosticChips from '@/components/tutor/DiagnosticChips'
import { useCompanion } from '@/hooks/useCompanion'
```

Dentro del componente, después del `useQuery` de `module`, añadir:

```tsx
  const { data: companion } = useCompanion()
```

- [ ] **Step 2: Insertar la franja entre el header y la lista de temas**

Justo después del `</div>` que cierra el bloque `{/* Header */}` y antes de `{/* Topics list */}`, insertar:

```tsx
      {/* Diagnóstico del companion: solo en el módulo actual del estudiante */}
      {companion?.position?.module_id === module.id && companion.diagnostic && (
        <section aria-label="Diagnóstico de tu avance" className="mb-6">
          <h2 className="text-sm font-semibold text-foreground mb-2">
            Tu diagnóstico en este módulo
          </h2>
          <DiagnosticChips diagnostic={companion.diagnostic} />
        </section>
      )}
```

- [ ] **Step 3: Verificar tipos**

Run: `cd C:\tutor-ia-rfa\frontend; npx tsc --noEmit`
Expected: sin errores

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/ModuleDetailPage.tsx
git commit -m "feat(companion): franja de diagnostico en detalle del modulo actual"
```

---

### Task 11: Suites completas + documentación + cierre

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Correr suite backend completa**

Run: `cd C:\tutor-ia-rfa\backend; python -m pytest tests/ -q`
Expected: 0 fallos (el guardián ISO `test_iso25010.py` incluido — los tests nuevos NO tocan la matriz)

- [ ] **Step 2: Correr suite frontend completa + build**

Run: `cd C:\tutor-ia-rfa\frontend; npx vitest run; npx tsc --noEmit; npm run build`
Expected: tests PASS, 0 errores de tipos, build verde

- [ ] **Step 3: Actualizar CLAUDE.md**

a) En la lista de fases (sección 🚀 SPRINTS, después de la entrada «ACOMPAÑAMIENTO PROACTIVO (Fase 4) ✅»), añadir:

```markdown
- **ACOMPAÑAMIENTO PROACTIVO (Fase 5) ✅** Companion «el sistema sigue al estudiante» (jun 2026): `services/companion_service.py` determinista (posición = primer módulo desbloqueado incompleto vía `compute_locks`; diagnóstico por bandas de quiz <60 repasar / 60-79 afianzar / ≥80 dominado, ≥2 intentos fallidos → repasar; next_action priorizado débil>pendiente>coding) + `GET /tutor/companion` (Redis TTL 60s). Frontend: `CompanionPanel` reemplaza hero del Dashboard (fallback al hero clásico si falla), burbuja preview en `FloatingTutor` (saludo contextual 1x/sesión, sessionStorage), `DiagnosticChips` en ModuleDetail. Sin LLM. Fuera de matriz ISO (33 RF congelados). Spec: `docs/superpowers/specs/2026-06-09-companion-seguimiento-design.md`.
```

b) En la sección 🔌 API REST, bajo `### /tutor`, añadir:

```markdown
- `GET /companion` → `{needs_assessment, position{module_id,module_title,progress_pct,topics_done,topics_total,course_completed}, greeting, diagnostic{weak[],practice[],next_action}, resources[≤3]}`. Posición del estudiante + diagnóstico determinista del módulo actual (Fase 5). Caché Redis TTL 60s. Sin LLM.
```

- [ ] **Step 4: Commit final**

```bash
git add CLAUDE.md
git commit -m "docs(companion): Fase 5 acompanamiento en CLAUDE.md (cronograma + API)"
```

- [ ] **Step 5: Verificación de cierre**

Run: `git log --oneline main..feat/companion-seguimiento`
Expected: ~10 commits (spec + 9 de implementación/docs). Rama lista para merge a main.

---

## Notas de diseño que el ejecutor NO debe «mejorar»

- **Determinista, sin LLM** — regla absoluta del proyecto para este motor.
- **`compute_locks` es la única fuente del desbloqueo secuencial** — no re-derivar.
- **Catálogo coding solamente** (`is_ai_generated == False`) en `has_coding_pending`: los desafíos AI per-usuario se regeneran y no son señal estable de pendiente.
- **Dominado ≥80 tiene precedencia** sobre la regla de ≥2 intentos fallidos (decisión del spec §3.1 «Dominado»).
- **No tocar** matriz ISO, `test_iso25010.py`, ni reportes OE5.
- Si `test_companion_requires_auth` devuelve 403 en vez de 401, la aserción `in (401, 403)` ya lo cubre — no cambiar el dep de auth.
