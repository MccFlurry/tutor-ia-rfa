# Tutor Nudges (Fase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir un motor determinista de "nudges" (mensajes proactivos del tutor) y mostrarlos en Dashboard y TopicPage, sin LLM.

**Architecture:** Lógica de reglas pura y testeable (`build_nudges`) separada de la obtención de datos (`gather_snapshot`). Un router expone `GET /api/v1/tutor/nudges?context=...`. Frontend consume vía hook TanStack Query y renderiza `<TutorNudge>`/`<TutorNudgeList>`. Las reglas leen estado ya existente (nivel, progreso, último quiz, inactividad, racha) — cero llamadas a Ollama.

**Tech Stack:** FastAPI + SQLAlchemy 2.0 async + Pydantic v2 + pytest (backend); React 18 + TypeScript + TanStack Query + Tailwind + Vitest/RTL (frontend).

**Scope note:** Fase 1 monta los nudges en Dashboard y Topic. Los contextos de resultado (`quiz_result`, `coding_result`, `assessment_result`) los consume **Fase 4** reusando este mismo motor; sus reglas se incluyen aquí pero el montaje en esas pantallas es Fase 4.

**Rutas frontend reales (para CTAs):** `/assessment`, `/modules`, `/modules/:id`, `/topics/:id`, `/quiz/:topicId`, `/coding/:challengeId`.

**Convención de ejecución:** rama `feat/tutor-nudges` desde `main`. Comandos backend desde `C:\tutor-ia-rfa\backend`; frontend desde `C:\tutor-ia-rfa\frontend`.

---

### Task 0: Crear rama de trabajo

- [ ] **Step 1: Crear rama desde main**

```bash
git checkout main
git checkout -b feat/tutor-nudges
```

---

### Task 1: Schema de Nudge + snapshot

**Files:**
- Create: `backend/app/schemas/tutor.py`

- [ ] **Step 1: Escribir el schema**

```python
"""schemas/tutor.py — Nudges proactivos del tutor (deterministas, sin LLM)."""
from dataclasses import dataclass
from pydantic import BaseModel


class Nudge(BaseModel):
    id: str          # id estable de la regla, p.ej. "no_level"
    tone: str        # info | success | warning | encourage
    icon: str        # nombre de icono lucide (ej. "compass", "rocket", "flame")
    title: str
    message: str
    cta_label: str | None = None
    cta_route: str | None = None


class NudgeResponse(BaseModel):
    nudges: list[Nudge]


@dataclass
class StudentSnapshot:
    """Estado del estudiante ya resuelto desde BD; insumo puro de build_nudges."""
    has_level: bool
    level: str | None
    overall_pct: float
    last_quiz_passed: bool | None
    last_quiz_topic_title: str | None
    last_quiz_topic_id: int | None
    days_inactive: int | None
    near_complete_module_title: str | None
    near_complete_module_id: int | None
    streak_days: int
```

- [ ] **Step 2: Verificar import**

Run: `python -c "from app.schemas.tutor import Nudge, NudgeResponse, StudentSnapshot; print('ok')"`
Expected: imprime `ok` (ejecutar desde `backend/` con el venv activo).

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/tutor.py
git commit -m "feat(tutor): agregar schemas Nudge y StudentSnapshot"
```

---

### Task 2: Motor de reglas puro `build_nudges`

**Files:**
- Create: `backend/app/services/tutor_service.py`
- Test: `backend/tests/unit/test_tutor_service.py`

- [ ] **Step 1: Escribir el test que falla**

```python
"""Unit tests del motor de nudges (puro, sin BD ni LLM)."""
from app.schemas.tutor import StudentSnapshot
from app.services.tutor_service import build_nudges


def _snap(**over):
    base = dict(
        has_level=True, level="beginner", overall_pct=40.0,
        last_quiz_passed=None, last_quiz_topic_title=None, last_quiz_topic_id=None,
        days_inactive=None, near_complete_module_title=None,
        near_complete_module_id=None, streak_days=0,
    )
    base.update(over)
    return StudentSnapshot(**base)


def test_no_level_returns_only_assessment_nudge():
    nudges = build_nudges(_snap(has_level=False, level=None), context="dashboard")
    assert len(nudges) == 1
    assert nudges[0].id == "no_level"
    assert nudges[0].cta_route == "/assessment"


def test_zero_progress_shows_welcome():
    nudges = build_nudges(_snap(overall_pct=0.0), context="dashboard")
    assert any(n.id == "welcome_start" for n in nudges)


def test_inactivity_shows_welcome_back_with_topic_cta():
    nudges = build_nudges(
        _snap(days_inactive=9, last_quiz_topic_title="Variables",
              last_quiz_topic_id=5),
        context="dashboard",
    )
    n = next(n for n in nudges if n.id == "inactive")
    assert n.cta_route == "/topics/5"
    assert "Variables" in n.message


def test_near_complete_module_nudge():
    nudges = build_nudges(
        _snap(near_complete_module_title="Kotlin", near_complete_module_id=2),
        context="dashboard",
    )
    n = next(n for n in nudges if n.id == "near_complete")
    assert n.cta_route == "/modules/2"


def test_streak_milestone_nudge():
    nudges = build_nudges(_snap(streak_days=7), context="dashboard")
    assert any(n.id == "streak_7" for n in nudges)


def test_no_streak_nudge_off_milestone():
    nudges = build_nudges(_snap(streak_days=4), context="dashboard")
    assert not any(n.id.startswith("streak_") for n in nudges)


def test_dashboard_caps_at_three_nudges():
    nudges = build_nudges(
        _snap(overall_pct=0.0, days_inactive=10, last_quiz_topic_id=1,
              last_quiz_topic_title="X", near_complete_module_title="M",
              near_complete_module_id=1, streak_days=7),
        context="dashboard",
    )
    assert len(nudges) <= 3


def test_topic_context_quiz_retry_nudge():
    nudges = build_nudges(
        _snap(last_quiz_passed=False, last_quiz_topic_title="Bucles",
              last_quiz_topic_id=8),
        context="topic", topic_id=8,
    )
    assert any(n.id == "quiz_retry" for n in nudges)
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run (desde `backend/`): `pytest tests/unit/test_tutor_service.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.services.tutor_service'`.

- [ ] **Step 3: Implementar el motor**

```python
"""services/tutor_service.py — Motor determinista de nudges proactivos.

build_nudges() es una función pura: recibe un StudentSnapshot ya resuelto
y el contexto de pantalla, devuelve los nudges aplicables. Sin BD ni LLM.
gather_snapshot()/get_nudges() (Task 3) resuelven el estado desde BD.
"""
from app.schemas.tutor import Nudge, StudentSnapshot

# Días de racha que disparan felicitación
STREAK_MILESTONES = (3, 7, 14, 30)
# Días sin actividad para considerar inactivo
INACTIVE_DAYS = 7
# Máximo de nudges en el dashboard (evita saturar)
DASHBOARD_MAX = 3


def build_nudges(
    snap: StudentSnapshot,
    context: str,
    *,
    topic_id: int | None = None,
    module_id: int | None = None,
    score: float | None = None,
) -> list[Nudge]:
    """Aplica las reglas deterministas y devuelve los nudges del contexto."""
    nudges: list[Nudge] = []

    # R1 — sin evaluación de entrada: bloquea todo lo demás
    if not snap.has_level:
        return [Nudge(
            id="no_level", tone="info", icon="compass",
            title="Empecemos por conocerte",
            message="Aún no realizas tu evaluación de entrada. Tómala para "
                    "personalizar tu ruta de aprendizaje.",
            cta_label="Ir a la evaluación", cta_route="/assessment",
        )]

    if context in ("dashboard", "module"):
        # R2 — progreso cero
        if snap.overall_pct <= 0:
            nudges.append(Nudge(
                id="welcome_start", tone="encourage", icon="rocket",
                title="¡Bienvenido a tu curso!",
                message="Comienza con el Módulo 1 para construir tus bases en "
                        "aplicaciones móviles.",
                cta_label="Empezar ahora", cta_route="/modules",
            ))

        # R3 — inactividad
        if snap.days_inactive is not None and snap.days_inactive >= INACTIVE_DAYS:
            msg = "¡Qué bueno verte de nuevo!"
            cta_label = None
            cta_route = None
            if snap.last_quiz_topic_title:
                msg += f" Retoma donde lo dejaste: «{snap.last_quiz_topic_title}»."
            if snap.last_quiz_topic_id:
                cta_label = "Continuar"
                cta_route = f"/topics/{snap.last_quiz_topic_id}"
            nudges.append(Nudge(
                id="inactive", tone="encourage", icon="hand",
                title="¡Bienvenido de vuelta!", message=msg,
                cta_label=cta_label, cta_route=cta_route,
            ))

        # R4 — módulo casi completo
        if snap.near_complete_module_title:
            nudges.append(Nudge(
                id="near_complete", tone="info", icon="flag",
                title="¡Estás muy cerca!",
                message=f"Te falta poco para terminar «{snap.near_complete_module_title}». "
                        "Termínalo y desbloquea el siguiente.",
                cta_label="Ver módulo",
                cta_route=f"/modules/{snap.near_complete_module_id}",
            ))

        # R5 — hito de racha
        if snap.streak_days in STREAK_MILESTONES:
            nudges.append(Nudge(
                id=f"streak_{snap.streak_days}", tone="success", icon="flame",
                title=f"¡Racha de {snap.streak_days} días!",
                message="Mantén el hábito; la constancia es clave para dominar "
                        "el desarrollo móvil.",
            ))

        return nudges[:DASHBOARD_MAX]

    if context == "topic":
        # R6 — último quiz reprobado en este tema → invitar a repasar/reintentar
        if (
            snap.last_quiz_passed is False
            and snap.last_quiz_topic_id is not None
            and (topic_id is None or topic_id == snap.last_quiz_topic_id)
        ):
            nudges.append(Nudge(
                id="quiz_retry", tone="warning", icon="repeat",
                title="Repasemos juntos",
                message="No aprobaste el último intento. Repasa el contenido y "
                        "vuelve a intentar el quiz; cada intento te acerca.",
                cta_label="Reintentar quiz",
                cta_route=f"/quiz/{snap.last_quiz_topic_id}",
            ))
        return nudges

    # contextos de resultado (quiz_result/coding_result/assessment_result) → Fase 4
    return nudges
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `pytest tests/unit/test_tutor_service.py -v`
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/tutor_service.py backend/tests/unit/test_tutor_service.py
git commit -m "feat(tutor): motor determinista de nudges con tests unitarios"
```

---

### Task 3: Obtención de snapshot desde BD + router

**Files:**
- Modify: `backend/app/services/tutor_service.py` (agregar `gather_snapshot` + `get_nudges`)
- Create: `backend/app/routers/tutor.py`
- Modify: `backend/app/main.py:95` (registrar router)
- Test: `backend/tests/integration/test_router_tutor.py`

- [ ] **Step 1: Escribir el test de integración que falla**

```python
"""Integration tests para /api/v1/tutor/nudges."""
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta

import pytest

from tests.integration.conftest import (
    result_scalar,
    result_scalar_one_or_none,
    result_rows,
)


@pytest.mark.asyncio
async def test_nudges_no_level(client, mock_db):
    # gather_snapshot: primer query = user level (None)
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(None),  # user level → has_level False corta aquí
    ]
    r = await client.get("/api/v1/tutor/nudges?context=dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["nudges"][0]["id"] == "no_level"


@pytest.mark.asyncio
async def test_nudges_dashboard_zero_progress(client, mock_db):
    level = SimpleNamespace(level="beginner")
    mock_db.execute.side_effect = [
        result_scalar_one_or_none(level),  # user level
        result_scalar(10),                 # total topics
        result_scalar(0),                  # completed
        result_rows([]),                   # last quiz attempt (join) → none
        result_rows([]),                   # last accessed progress → none
        result_rows([]),                   # modules progress rows → none
    ]
    r = await client.get("/api/v1/tutor/nudges?context=dashboard")
    assert r.status_code == 200
    ids = [n["id"] for n in r.json()["nudges"]]
    assert "welcome_start" in ids


@pytest.mark.asyncio
async def test_nudges_requires_context(client):
    r = await client.get("/api/v1/tutor/nudges")
    assert r.status_code == 422  # context es requerido
```

- [ ] **Step 2: Correr para verificar que falla**

Run: `pytest tests/integration/test_router_tutor.py -v`
Expected: FAIL (404 / ruta no existe).

- [ ] **Step 3: Agregar `gather_snapshot` + `get_nudges` al servicio**

Añadir al final de `backend/app/services/tutor_service.py`:

```python
from datetime import datetime, timezone

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_level import UserLevel
from app.models.topic import Topic
from app.models.module import Module
from app.models.progress import UserTopicProgress
from app.models.quiz import QuizAttempt
from app.services.progress_service import compute_streak

# Umbral de "módulo casi completo"
NEAR_COMPLETE_PCT = 80.0


async def gather_snapshot(
    user, db: AsyncSession, *, topic_id: int | None = None
) -> StudentSnapshot:
    """Resuelve el estado del estudiante desde BD (sin LLM)."""
    # 1. Nivel
    level_row = await db.execute(
        select(UserLevel).where(UserLevel.user_id == user.id)
    )
    level = level_row.scalar_one_or_none()
    if level is None:
        return StudentSnapshot(
            has_level=False, level=None, overall_pct=0.0,
            last_quiz_passed=None, last_quiz_topic_title=None,
            last_quiz_topic_id=None, days_inactive=None,
            near_complete_module_title=None, near_complete_module_id=None,
            streak_days=0,
        )

    # 2. Progreso global
    total_q = await db.execute(
        select(func.count(Topic.id)).where(Topic.is_active == True)  # noqa: E712
    )
    total = total_q.scalar() or 0
    done_q = await db.execute(
        select(func.count(UserTopicProgress.id))
        .join(Topic, Topic.id == UserTopicProgress.topic_id)
        .where(
            UserTopicProgress.user_id == user.id,
            UserTopicProgress.is_completed == True,  # noqa: E712
            Topic.is_active == True,  # noqa: E712
        )
    )
    done = done_q.scalar() or 0
    overall_pct = round(done / total * 100, 1) if total else 0.0

    # 3. Último intento de quiz
    last_quiz_q = await db.execute(
        select(QuizAttempt, Topic)
        .join(Topic, Topic.id == QuizAttempt.topic_id)
        .where(QuizAttempt.user_id == user.id)
        .order_by(desc(QuizAttempt.attempted_at))
        .limit(1)
    )
    lq = last_quiz_q.first()
    last_quiz_passed = lq[0].is_passed if lq else None
    last_quiz_topic_title = lq[1].title if lq else None
    last_quiz_topic_id = lq[1].id if lq else None

    # 4. Inactividad (último acceso a cualquier tema)
    last_acc_q = await db.execute(
        select(UserTopicProgress.last_accessed_at)
        .where(UserTopicProgress.user_id == user.id)
        .order_by(desc(UserTopicProgress.last_accessed_at))
        .limit(1)
    )
    last_acc = last_acc_q.first()
    days_inactive = None
    if last_acc and last_acc[0]:
        delta = datetime.now(timezone.utc) - last_acc[0]
        days_inactive = delta.days

    # 5. Módulo casi completo (mayor pct < 100 y ≥ umbral)
    near_title = None
    near_id = None
    mod_rows = await db.execute(
        select(
            Module.id, Module.title,
            func.count(Topic.id).label("total"),
            func.count(UserTopicProgress.id).filter(
                UserTopicProgress.is_completed == True  # noqa: E712
            ).label("done"),
        )
        .join(Topic, Topic.module_id == Module.id)
        .outerjoin(
            UserTopicProgress,
            (UserTopicProgress.topic_id == Topic.id)
            & (UserTopicProgress.user_id == user.id),
        )
        .where(Module.is_active == True, Topic.is_active == True)  # noqa: E712
        .group_by(Module.id, Module.title)
        .order_by(Module.order_index)
    )
    best_pct = 0.0
    for mid, mtitle, mtotal, mdone in mod_rows.all():
        pct = round((mdone or 0) / mtotal * 100, 1) if mtotal else 0.0
        if NEAR_COMPLETE_PCT <= pct < 100 and pct > best_pct:
            best_pct, near_title, near_id = pct, mtitle, mid

    # 6. Racha (reusa servicio existente)
    streak = await compute_streak(user.id, db)
    streak_days = getattr(streak, "current", 0) if streak else 0

    return StudentSnapshot(
        has_level=True, level=level.level, overall_pct=overall_pct,
        last_quiz_passed=last_quiz_passed,
        last_quiz_topic_title=last_quiz_topic_title,
        last_quiz_topic_id=last_quiz_topic_id,
        days_inactive=days_inactive,
        near_complete_module_title=near_title,
        near_complete_module_id=near_id,
        streak_days=streak_days,
    )


async def get_nudges(
    user, db: AsyncSession, context: str, *,
    topic_id: int | None = None, module_id: int | None = None,
    score: float | None = None,
) -> list[Nudge]:
    snap = await gather_snapshot(user, db, topic_id=topic_id)
    return build_nudges(
        snap, context, topic_id=topic_id, module_id=module_id, score=score
    )
```

> Nota: si `compute_streak` devuelve otra forma (dict/objeto), ajustar `getattr(streak, "current", 0)`. Verificar firma en `app/services/progress_service.py` antes de implementar.

- [ ] **Step 4: Crear el router**

```python
"""routers/tutor.py — Nudges proactivos del tutor (deterministas)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_redis
from app.models.user import User
from app.schemas.tutor import NudgeResponse
from app.services.tutor_service import get_nudges
from app.utils.cache import cached_json

router = APIRouter(prefix="/tutor", tags=["tutor"])

# Contextos cuyo resultado depende de un intento recién hecho → no cachear
_NO_CACHE = {"quiz_result", "coding_result", "assessment_result"}
NUDGE_CACHE_TTL = 30  # seconds


@router.get("/nudges", response_model=NudgeResponse)
async def get_tutor_nudges(
    context: str = Query(..., description="dashboard|topic|module|*_result"),
    topic_id: int | None = None,
    module_id: int | None = None,
    score: float | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    async def _build() -> dict:
        nudges = await get_nudges(
            current_user, db, context,
            topic_id=topic_id, module_id=module_id, score=score,
        )
        return NudgeResponse(nudges=nudges).model_dump(mode="json")

    if context in _NO_CACHE:
        payload = await _build()
    else:
        key = f"nudges:{current_user.id}:{context}:{topic_id}:{module_id}"
        payload = await cached_json(
            redis_client, key, ttl=NUDGE_CACHE_TTL, loader=_build
        )
    return NudgeResponse.model_validate(payload)
```

- [ ] **Step 5: Registrar el router en main.py**

En `backend/app/main.py`, junto a los demás `include_router` (después de la línea 95):

```python
from app.routers import tutor  # añadir al bloque de imports de routers
app.include_router(tutor.router, prefix="/api/v1")
```

- [ ] **Step 6: Correr los tests de integración**

Run: `pytest tests/integration/test_router_tutor.py -v`
Expected: PASS (3 tests). Si `test_nudges_dashboard_zero_progress` desfasa por el número de queries, ajustar el `side_effect` al orden real de `gather_snapshot`.

- [ ] **Step 7: Correr toda la suite backend (no romper nada)**

Run: `pytest -q`
Expected: PASS, sin regresiones; cobertura ≥80%.

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/tutor_service.py backend/app/routers/tutor.py backend/app/main.py backend/tests/integration/test_router_tutor.py
git commit -m "feat(tutor): endpoint GET /tutor/nudges con snapshot desde BD"
```

---

### Task 4: Tipos + cliente API + hook (frontend)

**Files:**
- Create: `frontend/src/types/tutor.ts`
- Create: `frontend/src/api/tutor.ts`
- Create: `frontend/src/hooks/useTutorNudges.ts`

- [ ] **Step 1: Crear tipos**

```typescript
// frontend/src/types/tutor.ts
export type NudgeTone = 'info' | 'success' | 'warning' | 'encourage'

export interface Nudge {
  id: string
  tone: NudgeTone
  icon: string
  title: string
  message: string
  cta_label?: string | null
  cta_route?: string | null
}

export interface NudgeResponse {
  nudges: Nudge[]
}

export type NudgeContext =
  | 'dashboard'
  | 'topic'
  | 'module'
  | 'quiz_result'
  | 'coding_result'
  | 'assessment_result'
```

- [ ] **Step 2: Crear cliente API** (sigue el patrón de `api/dashboard.ts`)

```typescript
// frontend/src/api/tutor.ts
import apiClient from './client'
import type { NudgeResponse, NudgeContext } from '@/types/tutor'

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
}
```

- [ ] **Step 3: Crear hook** (sigue el patrón de `hooks/useChat.ts`)

```typescript
// frontend/src/hooks/useTutorNudges.ts
import { useQuery } from '@tanstack/react-query'
import { tutorApi, type NudgeParams } from '@/api/tutor'

export function useTutorNudges(params: NudgeParams) {
  return useQuery({
    queryKey: ['tutor-nudges', params.context, params.topicId, params.moduleId, params.score],
    queryFn: async () => {
      const { data } = await tutorApi.getNudges(params)
      return data.nudges
    },
  })
}
```

- [ ] **Step 4: Verificar compilación de tipos**

Run (desde `frontend/`): `npx tsc --noEmit`
Expected: sin errores.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/tutor.ts frontend/src/api/tutor.ts frontend/src/hooks/useTutorNudges.ts
git commit -m "feat(tutor): tipos, cliente API y hook de nudges (frontend)"
```

---

### Task 5: Componente `<TutorNudge>` + test

**Files:**
- Create: `frontend/src/components/tutor/TutorNudge.tsx`
- Test: `frontend/src/components/tutor/TutorNudge.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

```typescript
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import TutorNudge from './TutorNudge'
import type { Nudge } from '@/types/tutor'

function renderNudge(over: Partial<Nudge> = {}) {
  const nudge: Nudge = {
    id: 'welcome_start', tone: 'encourage', icon: 'rocket',
    title: '¡Bienvenido!', message: 'Empieza con el Módulo 1.',
    cta_label: 'Empezar', cta_route: '/modules', ...over,
  }
  return render(
    <MemoryRouter>
      <TutorNudge nudge={nudge} />
    </MemoryRouter>
  )
}

describe('<TutorNudge />', () => {
  it('renders title and message', () => {
    renderNudge()
    expect(screen.getByText('¡Bienvenido!')).toBeInTheDocument()
    expect(screen.getByText('Empieza con el Módulo 1.')).toBeInTheDocument()
  })

  it('renders CTA link when cta_route present', () => {
    renderNudge()
    const link = screen.getByRole('link', { name: 'Empezar' })
    expect(link).toHaveAttribute('href', '/modules')
  })

  it('omits CTA when no cta_route', () => {
    renderNudge({ cta_label: null, cta_route: null })
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr para verificar que falla**

Run (desde `frontend/`): `npx vitest run src/components/tutor/TutorNudge.test.tsx`
Expected: FAIL (módulo no existe).

- [ ] **Step 3: Implementar el componente**

```tsx
// frontend/src/components/tutor/TutorNudge.tsx
import { Link } from 'react-router-dom'
import { Compass, Rocket, Hand, Flag, Flame, Repeat, Sparkles } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { Nudge, NudgeTone } from '@/types/tutor'

const ICONS: Record<string, LucideIcon> = {
  compass: Compass, rocket: Rocket, hand: Hand,
  flag: Flag, flame: Flame, repeat: Repeat,
}

// Clases por tono usando tokens semánticos (dark-mode safe)
const TONE: Record<NudgeTone, string> = {
  info: 'border-primary/30 bg-primary/5',
  success: 'border-green-500/30 bg-green-500/5',
  warning: 'border-amber-500/30 bg-amber-500/5',
  encourage: 'border-primary/30 bg-primary/5',
}

export default function TutorNudge({ nudge }: { nudge: Nudge }) {
  const Icon = ICONS[nudge.icon] ?? Sparkles
  return (
    <div
      className={`flex gap-3 rounded-lg border p-4 ${TONE[nudge.tone]}`}
      role="status"
    >
      <Icon className="h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
      <div className="flex-1 space-y-1">
        <p className="font-semibold text-foreground">{nudge.title}</p>
        <p className="text-sm text-muted-foreground">{nudge.message}</p>
        {nudge.cta_route && nudge.cta_label && (
          <Link
            to={nudge.cta_route}
            className="inline-flex min-h-[44px] items-center text-sm font-medium text-primary hover:underline"
          >
            {nudge.cta_label}
          </Link>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Correr para verificar que pasa**

Run: `npx vitest run src/components/tutor/TutorNudge.test.tsx`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/tutor/TutorNudge.tsx frontend/src/components/tutor/TutorNudge.test.tsx
git commit -m "feat(tutor): componente TutorNudge con test"
```

---

### Task 6: `<TutorNudgeList>` + montaje en Dashboard y Topic

**Files:**
- Create: `frontend/src/components/tutor/TutorNudgeList.tsx`
- Modify: `frontend/src/pages/DashboardPage.tsx`
- Modify: `frontend/src/pages/TopicPage.tsx`

- [ ] **Step 1: Crear la lista**

```tsx
// frontend/src/components/tutor/TutorNudgeList.tsx
import TutorNudge from './TutorNudge'
import { useTutorNudges } from '@/hooks/useTutorNudges'
import type { NudgeContext } from '@/types/tutor'

interface Props {
  context: NudgeContext
  topicId?: number
  moduleId?: number
  score?: number
}

export default function TutorNudgeList({ context, topicId, moduleId, score }: Props) {
  const { data: nudges } = useTutorNudges({ context, topicId, moduleId, score })
  if (!nudges || nudges.length === 0) return null
  return (
    <div className="space-y-3" aria-label="Mensajes del tutor">
      {nudges.map((n) => (
        <TutorNudge key={n.id} nudge={n} />
      ))}
    </div>
  )
}
```

- [ ] **Step 2: Montar en DashboardPage**

En `frontend/src/pages/DashboardPage.tsx`: importar y renderizar cerca del tope del contenido (debajo del saludo, antes de las recomendaciones).

```tsx
import TutorNudgeList from '@/components/tutor/TutorNudgeList'
// ...dentro del JSX, tras el encabezado de bienvenida:
<TutorNudgeList context="dashboard" />
```

- [ ] **Step 3: Montar en TopicPage**

En `frontend/src/pages/TopicPage.tsx`: obtener el `id` del tema desde `useParams` (ya usado en la página) y renderizar arriba del contenido del tema.

```tsx
import TutorNudgeList from '@/components/tutor/TutorNudgeList'
// ...el id numérico del tema actual (Number(id)):
<TutorNudgeList context="topic" topicId={Number(topicId)} />
```

> Verificar el nombre real del param (`id`) en `TopicPage.tsx` y convertir a número.

- [ ] **Step 4: Verificar build**

Run (desde `frontend/`): `npx tsc --noEmit && npx vitest run`
Expected: tsc sin errores; toda la suite de tests pasa.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/tutor/TutorNudgeList.tsx frontend/src/pages/DashboardPage.tsx frontend/src/pages/TopicPage.tsx
git commit -m "feat(tutor): TutorNudgeList montado en Dashboard y Topic"
```

---

### Task 7: Documentación + matriz ISO

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/matriz-trazabilidad-ISO25010.md`

- [ ] **Step 1: Registrar la fase en CLAUDE.md**

Agregar bajo el resumen de sprints/fases una entrada de "Fase de acompañamiento proactivo (Fase 1: nudges)" describiendo: motor determinista, endpoint `GET /tutor/nudges`, montaje Dashboard/Topic, encuadre como modelo de interacción/pedagógico (insumo OE3/OE5), sin nuevo OE. Documentar el endpoint en la sección API REST (`/tutor`).

- [ ] **Step 2: Sumar RF de acompañamiento a la matriz ISO**

En `docs/matriz-trazabilidad-ISO25010.md` agregar fila(s): nuevo RF "Acompañamiento proactivo del tutor" ↔ caso de prueba `test_tutor_service.py` / `test_router_tutor.py` ↔ subcaracterística *Pertinencia funcional / Operabilidad*.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md docs/matriz-trazabilidad-ISO25010.md
git commit -m "docs(tutor): registrar Fase 1 de acompañamiento y RF en matriz ISO"
```

---

## Verificación final de Fase 1

- [ ] `pytest -q` verde (sin regresiones, cobertura ≥80%).
- [ ] `npx tsc --noEmit` sin errores y `npx vitest run` verde.
- [ ] `GET /api/v1/tutor/nudges?context=dashboard` responde nudges coherentes con el estado.
- [ ] Dashboard y TopicPage muestran nudges del tutor.
- [ ] CLAUDE.md y matriz ISO actualizados.

Al cerrar Fase 1, decidir con el usuario si seguir con Fase 2 (asistente flotante) — plan propio.
