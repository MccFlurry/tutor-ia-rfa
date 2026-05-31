# Banco de Recursos Curados (Fase 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Banco de recursos de aprendizaje (videos YouTube, libros, artículos) curados por admin, mostrados al estudiante por módulo/tema — lo que el jurado pidió ("links de libros o videos").

**Architecture:** Nueva tabla `learning_resources` (módulo/tema, tipo, url, etc.). Endpoint estudiante `GET /resources` (solo lectura, activos). CRUD admin bajo `/admin/resources`. Frontend: `ResourceCard`/`ResourceList` montados en Dashboard (recursos del módulo recomendado) y Topic (recursos del tema), + pestaña "Recursos" en AdminPage. Seed con URLs **marcadas para verificación humana** (regla CLAUDE "no inventa" / verificación externa).

**Tech Stack:** FastAPI + SQLAlchemy 2.0 async + Alembic + Pydantic v2 + pytest; React 18 + TS + Tailwind + TanStack Query + Vitest/RTL.

**Constraint:** El LLM NUNCA genera ni recomienda recursos. Todo es curado por admin; las URLs del seed quedan explícitamente marcadas para que un humano las verifique.

**Convención:** rama `feat/tutor-recursos` desde `main`. Backend desde `C:\tutor-ia-rfa\backend`, frontend desde `C:\tutor-ia-rfa\frontend`. Migraciones llegan hasta `005_ai_quiz_sessions` → esta es `006`.

---

### Task 0: Crear rama

- [ ] **Step 1:**
```bash
git checkout main
git checkout -b feat/tutor-recursos
```

---

### Task 1: Migración 006 + modelo `LearningResource`

**Files:**
- Create: `backend/alembic/versions/006_add_learning_resources.py`
- Create: `backend/app/models/learning_resource.py`

- [ ] **Step 1: Crear la migración** (sigue el patrón de `005_add_ai_quiz_sessions.py`)

```python
"""Add learning_resources table (curated videos/books per module/topic).

Revision ID: 006_learning_resources
Revises: 005_ai_quiz_sessions
Create Date: 2026-05-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006_learning_resources"
down_revision: Union[str, None] = "005_ai_quiz_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "learning_resources",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "module_id", sa.Integer,
            sa.ForeignKey("modules.id", ondelete="CASCADE"), nullable=True,
        ),
        sa.Column(
            "topic_id", sa.Integer,
            sa.ForeignKey("topics.id", ondelete="CASCADE"), nullable=True,
        ),
        sa.Column("kind", sa.String(20), nullable=False),  # video|book|article|doc
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"), nullable=True,
        ),
        sa.Column(
            "created_at", postgresql.TIMESTAMP(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_resources_module", "learning_resources", ["module_id"])
    op.create_index("idx_resources_topic", "learning_resources", ["topic_id"])


def downgrade() -> None:
    op.drop_index("idx_resources_topic")
    op.drop_index("idx_resources_module")
    op.drop_table("learning_resources")
```

- [ ] **Step 2: Crear el modelo** (sigue el patrón de `models/assessment_bank.py`)

```python
import uuid
from datetime import datetime, timezone

from sqlalchemy import Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

from app.database import Base


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("modules.id", ondelete="CASCADE"), nullable=True
    )
    topic_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # video|book|article|doc
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    module = relationship("Module")
    topic = relationship("Topic")
```

- [ ] **Step 3: Verificar import del modelo**

Run (desde `backend/`): `python -c "from app.models.learning_resource import LearningResource; print('ok')"`
Expected: `ok`.

- [ ] **Step 4: Verificar que la migración aplica** (si hay Postgres dev arriba en `localhost:5433`)

Run (desde `backend/`): `alembic upgrade head`
Expected: aplica `006_learning_resources` sin error. Si no hay BD disponible en este entorno, omitir y anotar que la migración debe correrse al desplegar; la validación de sintaxis basta (`python -c "import alembic.versions..."` no aplica — revisar visualmente que `revision`/`down_revision` encadenan con 005).

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/versions/006_add_learning_resources.py backend/app/models/learning_resource.py
git commit -m "feat(resources): migracion 006 + modelo LearningResource"
```

---

### Task 2: Schemas + endpoint estudiante `GET /resources`

**Files:**
- Create: `backend/app/schemas/learning_resource.py`
- Create: `backend/app/routers/resources.py`
- Modify: `backend/app/main.py` (registrar router)
- Test: `backend/tests/integration/test_router_resources.py`

- [ ] **Step 1: Crear schemas**

```python
"""schemas/learning_resource.py — Recursos de aprendizaje curados."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

ResourceKind = Literal["video", "book", "article", "doc"]


class LearningResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    module_id: int | None
    topic_id: int | None
    kind: str
    title: str
    url: str
    author: str | None
    description: str | None
    order_index: int
    is_active: bool


class LearningResourceCreate(BaseModel):
    module_id: int | None = None
    topic_id: int | None = None
    kind: ResourceKind
    title: str
    url: str
    author: str | None = None
    description: str | None = None
    order_index: int = 0


class LearningResourceUpdate(BaseModel):
    module_id: int | None = None
    topic_id: int | None = None
    kind: ResourceKind | None = None
    title: str | None = None
    url: str | None = None
    author: str | None = None
    description: str | None = None
    order_index: int | None = None
    is_active: bool | None = None
```

- [ ] **Step 2: Escribir el test de integración que falla**

```python
"""Integration tests para /api/v1/resources (estudiante)."""
from types import SimpleNamespace

import pytest

from tests.integration.conftest import result_scalars_all


def _res(id_=1, kind="video"):
    return SimpleNamespace(
        id=id_, module_id=1, topic_id=None, kind=kind,
        title="Kotlin Basics", url="https://youtu.be/abc", author="Google",
        description=None, order_index=0, is_active=True,
    )


@pytest.mark.asyncio
async def test_list_resources_by_module(client, mock_db):
    mock_db.execute.side_effect = [result_scalars_all([_res()])]
    r = await client.get("/api/v1/resources?module_id=1")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["kind"] == "video"
    assert body[0]["url"] == "https://youtu.be/abc"


@pytest.mark.asyncio
async def test_list_resources_empty(client, mock_db):
    mock_db.execute.side_effect = [result_scalars_all([])]
    r = await client.get("/api/v1/resources?topic_id=5")
    assert r.status_code == 200
    assert r.json() == []
```

- [ ] **Step 3: Correr para verificar que falla**

Run (desde `backend/`): `pytest tests/integration/test_router_resources.py -v`
Expected: FAIL (404 ruta no existe).

- [ ] **Step 4: Crear el router estudiante**

```python
"""routers/resources.py — Recursos de aprendizaje (lectura para estudiantes)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.learning_resource import LearningResource
from app.schemas.learning_resource import LearningResourceResponse

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("", response_model=list[LearningResourceResponse])
async def list_resources(
    module_id: int | None = Query(None),
    topic_id: int | None = Query(None),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Recursos activos filtrados por módulo y/o tema, ordenados."""
    query = select(LearningResource).where(LearningResource.is_active == True)  # noqa: E712
    if topic_id is not None:
        query = query.where(LearningResource.topic_id == topic_id)
    if module_id is not None:
        query = query.where(LearningResource.module_id == module_id)
    query = query.order_by(LearningResource.order_index, LearningResource.id)
    result = await db.execute(query)
    return [LearningResourceResponse.model_validate(r) for r in result.scalars().all()]
```

- [ ] **Step 5: Registrar router en main.py** — agregar `resources` al import de routers y `app.include_router(resources.router, prefix="/api/v1")` junto a los demás.

- [ ] **Step 6: Correr el test** → 2 PASS. Luego `pytest -q` (sin regresiones).

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/learning_resource.py backend/app/routers/resources.py backend/app/main.py backend/tests/integration/test_router_resources.py
git commit -m "feat(resources): schemas + endpoint estudiante GET /resources"
```

---

### Task 3: CRUD admin de recursos

**Files:**
- Modify: `backend/app/routers/admin.py` (agregar sección "Learning Resources CRUD")
- Test: `backend/tests/integration/test_router_admin.py` (agregar tests si el archivo existe; si no, crear `test_router_admin_resources.py`)

- [ ] **Step 1: Escribir tests admin que fallan**

Crear `backend/tests/integration/test_router_admin_resources.py`:

```python
"""Integration tests para CRUD admin de /admin/resources."""
from types import SimpleNamespace

import pytest

from tests.integration.conftest import result_scalars_all, result_scalar_one_or_none


def _res(id_=1):
    return SimpleNamespace(
        id=id_, module_id=1, topic_id=None, kind="video",
        title="X", url="https://youtu.be/x", author=None,
        description=None, order_index=0, is_active=True,
    )


@pytest.mark.asyncio
async def test_admin_list_resources(admin_client, mock_db):
    mock_db.execute.side_effect = [result_scalars_all([_res()])]
    r = await admin_client.get("/api/v1/admin/resources")
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_admin_create_resource(admin_client, mock_db):
    # create flushes/commits then returns the ORM object
    r = await admin_client.post("/api/v1/admin/resources", json={
        "module_id": 1, "kind": "video", "title": "Nuevo",
        "url": "https://youtu.be/new",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "Nuevo"
    assert body["kind"] == "video"


@pytest.mark.asyncio
async def test_admin_create_resource_requires_admin(client):
    # 'client' is a student → 403
    r = await client.post("/api/v1/admin/resources", json={
        "kind": "video", "title": "x", "url": "https://y",
    })
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_delete_resource_404(admin_client, mock_db):
    mock_db.execute.side_effect = [result_scalar_one_or_none(None)]
    r = await admin_client.delete("/api/v1/admin/resources/999")
    assert r.status_code == 404
```

> Nota: el POST devuelve el objeto recién creado. Como `mock_db.add`/`flush`/`commit` son mocks, el endpoint debe construir la respuesta desde el objeto ORM en memoria (igual que `create_bank_item`), por lo que `id` puede venir `None` en el test; por eso el test sólo asserta `title`/`kind`. Asegúrate de que `LearningResourceResponse.model_validate(item)` tolere `id=None` — si el schema exige `id: int`, en el test el objeto tendrá `id=None` y fallará validación. Para evitarlo, en el test el create no mockea `id`; ajusta el endpoint para `await db.refresh(item)` NO es posible con mock. **Solución:** en el endpoint, tras `flush`, el `item.id` sigue None bajo mock. Para que el test pase, haz que el POST devuelva `LearningResourceResponse` con los campos del request + `id` del item (None bajo mock) y cambia el schema de respuesta del POST a tolerar `id: int | None`, O — más simple y consistente con `create_bank_item` (que NO es testeado con asserts de id) — en el test NO assertes `id`. Mantener `id: int` en el response y, en el test, parchear `mock_db.refresh` para asignar un id:
>
> ```python
> async def _fake_refresh(obj):
>     obj.id = 1
> mock_db.refresh.side_effect = _fake_refresh
> ```
> y que el endpoint llame `await db.refresh(item)` tras commit. Incluye esa línea en el endpoint create (paso 2) y el `refresh` mock en el test create. Esto es más limpio que debilitar el schema.

- [ ] **Step 2: Agregar el CRUD admin** en `backend/app/routers/admin.py`

Importar arriba: `from app.models.learning_resource import LearningResource` y `from app.schemas.learning_resource import (LearningResourceResponse, LearningResourceCreate, LearningResourceUpdate)`.

Agregar una sección nueva (después de la de Assessment Bank, mismo estilo):

```python
# ==========================================================
# Learning Resources CRUD (videos/libros curados — Fase 3)
# ==========================================================

@router.get("/resources", response_model=list[LearningResourceResponse])
async def list_resources_admin(
    module_id: int | None = Query(None),
    topic_id: int | None = Query(None),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(LearningResource)
    if module_id is not None:
        query = query.where(LearningResource.module_id == module_id)
    if topic_id is not None:
        query = query.where(LearningResource.topic_id == topic_id)
    query = query.order_by(LearningResource.module_id, LearningResource.order_index, LearningResource.id)
    result = await db.execute(query)
    return [LearningResourceResponse.model_validate(r) for r in result.scalars().all()]


@router.post("/resources", response_model=LearningResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    data: LearningResourceCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    item = LearningResource(
        module_id=data.module_id,
        topic_id=data.topic_id,
        kind=data.kind,
        title=data.title,
        url=data.url,
        author=data.author,
        description=data.description,
        order_index=data.order_index,
        created_by=admin.id,
        is_active=True,
    )
    db.add(item)
    await db.flush()
    await db.commit()
    await db.refresh(item)
    return LearningResourceResponse.model_validate(item)


@router.put("/resources/{resource_id}", response_model=LearningResourceResponse)
async def update_resource(
    resource_id: int,
    data: LearningResourceUpdate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(LearningResource).where(LearningResource.id == resource_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurso no encontrado")
    for field in ("module_id", "topic_id", "kind", "title", "url", "author", "description", "order_index", "is_active"):
        value = getattr(data, field)
        if value is not None:
            setattr(item, field, value)
    await db.flush()
    await db.commit()
    await db.refresh(item)
    return LearningResourceResponse.model_validate(item)


@router.delete("/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: int,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(LearningResource).where(LearningResource.id == resource_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurso no encontrado")
    await db.delete(item)
    await db.commit()
```

> En el test create, mockear `mock_db.refresh` con el `_fake_refresh` mostrado arriba para que `item.id=1`. (El conftest `mock_db.refresh` es un `AsyncMock`; setéale `.side_effect = _fake_refresh` en ese test.)

- [ ] **Step 3:** `pytest tests/integration/test_router_admin_resources.py -v` → 4 PASS. Luego `pytest -q` sin regresiones.

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/admin.py backend/tests/integration/test_router_admin_resources.py
git commit -m "feat(resources): CRUD admin /admin/resources"
```

---

### Task 4: Seed de recursos (URLs marcadas para verificación humana)

**Files:**
- Create: `backend/scripts/seed_learning_resources.py`

- [ ] **Step 1: Crear el seed** (sigue el patrón de `seed_assessment_bank.py`, idempotente)

```python
"""
seed_learning_resources.py — Carga recursos de aprendizaje curados
(videos/libros) por módulo. Idempotente: skip si ya hay recursos.

⚠️  URLs DE EJEMPLO — VERIFICAR MANUALMENTE antes de usar en producción.
    El sistema NUNCA inventa recursos vía LLM; este seed es un punto de
    partida que un docente/admin debe revisar y completar.

Ejecutar:
    docker compose exec backend python /app/scripts/seed_learning_resources.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.user import User
from app.models.learning_resource import LearningResource

engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ⚠️ PLACEHOLDERS — el admin debe verificar/reemplazar estas URLs.
RESOURCES_BY_MODULE = {
    1: [
        {"kind": "video", "title": "Introducción a Android y Kotlin (verificar URL)",
         "url": "https://www.youtube.com/results?search_query=introduccion+android+kotlin+espanol",
         "author": "Pendiente de verificación", "order_index": 0},
        {"kind": "book", "title": "Bibliografía del sílabo M1 (completar)",
         "url": "https://developer.android.com/courses", "author": "Android Developers", "order_index": 1},
    ],
    2: [
        {"kind": "video", "title": "Fundamentos de Kotlin (verificar URL)",
         "url": "https://www.youtube.com/results?search_query=kotlin+fundamentos+espanol",
         "author": "Pendiente de verificación", "order_index": 0},
    ],
    3: [
        {"kind": "doc", "title": "Guía oficial de layouts (Android Developers)",
         "url": "https://developer.android.com/develop/ui", "author": "Android Developers", "order_index": 0},
    ],
    4: [
        {"kind": "doc", "title": "Room + APIs REST (Android Developers)",
         "url": "https://developer.android.com/training/data-storage/room", "author": "Android Developers", "order_index": 0},
    ],
    5: [
        {"kind": "doc", "title": "Publicación en Play Store (verificar)",
         "url": "https://developer.android.com/distribute", "author": "Android Developers", "order_index": 0},
    ],
}


async def seed():
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(LearningResource))
        if existing.scalars().first():
            print("Ya hay recursos. Nada que hacer.")
            return
        admin_result = await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
        admin = admin_result.scalar_one_or_none()
        created_by = admin.id if admin else None
        total = 0
        for module_id, items in RESOURCES_BY_MODULE.items():
            for item in items:
                db.add(LearningResource(
                    module_id=module_id, topic_id=None,
                    kind=item["kind"], title=item["title"], url=item["url"],
                    author=item.get("author"), description=item.get("description"),
                    order_index=item.get("order_index", 0),
                    created_by=created_by, is_active=True,
                ))
                total += 1
        await db.commit()
        print(f"Recursos sembrados: {total}")
        print("⚠️  RECUERDA: verifica/reemplaza las URLs placeholder en el panel admin.")


if __name__ == "__main__":
    asyncio.run(seed())
```

- [ ] **Step 2: Verificar import/sintaxis**

Run (desde `backend/`): `python -c "import scripts.seed_learning_resources; print('ok')"`
Expected: `ok` (no ejecuta el seed, sólo importa).

- [ ] **Step 3: Commit**

```bash
git add backend/scripts/seed_learning_resources.py
git commit -m "feat(resources): seed inicial (URLs marcadas para verificacion humana)"
```

---

### Task 5: Frontend — tipos + api estudiante + hook

**Files:**
- Create: `frontend/src/types/resource.ts`
- Create: `frontend/src/api/resources.ts`
- Create: `frontend/src/hooks/useResources.ts`

- [ ] **Step 1: tipos**

```typescript
// frontend/src/types/resource.ts
export type ResourceKind = 'video' | 'book' | 'article' | 'doc'

export interface LearningResource {
  id: number
  module_id: number | null
  topic_id: number | null
  kind: ResourceKind
  title: string
  url: string
  author?: string | null
  description?: string | null
  order_index: number
  is_active: boolean
}
```

- [ ] **Step 2: api** (patrón de `api/dashboard.ts`)

```typescript
// frontend/src/api/resources.ts
import apiClient from './client'
import type { LearningResource } from '@/types/resource'

export const resourcesApi = {
  list: (params: { moduleId?: number; topicId?: number }) =>
    apiClient.get<LearningResource[]>('/resources', {
      params: { module_id: params.moduleId, topic_id: params.topicId },
    }),
}
```

- [ ] **Step 3: hook** (patrón de `hooks/useChat.ts`)

```typescript
// frontend/src/hooks/useResources.ts
import { useQuery } from '@tanstack/react-query'
import { resourcesApi } from '@/api/resources'

export function useResources(params: { moduleId?: number; topicId?: number }) {
  const enabled = params.moduleId != null || params.topicId != null
  return useQuery({
    queryKey: ['resources', params.moduleId, params.topicId],
    queryFn: async () => {
      const { data } = await resourcesApi.list(params)
      return data
    },
    enabled,
    staleTime: 60_000,
  })
}
```

- [ ] **Step 4:** `npx tsc --noEmit` (desde `frontend/`) → sin errores.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/resource.ts frontend/src/api/resources.ts frontend/src/hooks/useResources.ts
git commit -m "feat(resources): tipos, api y hook (frontend)"
```

---

### Task 6: `ResourceCard` + `ResourceList` + test

**Files:**
- Create: `frontend/src/components/resources/ResourceCard.tsx`
- Create: `frontend/src/components/resources/ResourceList.tsx`
- Test: `frontend/src/components/resources/ResourceCard.test.tsx`

- [ ] **Step 1: test que falla**

```tsx
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import ResourceCard from './ResourceCard'
import type { LearningResource } from '@/types/resource'

function renderCard(over: Partial<LearningResource> = {}) {
  const r: LearningResource = {
    id: 1, module_id: 1, topic_id: null, kind: 'video',
    title: 'Kotlin Basics', url: 'https://youtu.be/abc',
    author: 'Google', description: null, order_index: 0, is_active: true, ...over,
  }
  return render(<ResourceCard resource={r} />)
}

describe('<ResourceCard />', () => {
  it('renders title and author', () => {
    renderCard()
    expect(screen.getByText('Kotlin Basics')).toBeInTheDocument()
    expect(screen.getByText(/Google/)).toBeInTheDocument()
  })

  it('links to the url, opening in a new tab safely', () => {
    renderCard()
    const link = screen.getByRole('link', { name: /Kotlin Basics/ })
    expect(link).toHaveAttribute('href', 'https://youtu.be/abc')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', expect.stringContaining('noopener'))
  })
})
```

- [ ] **Step 2:** `npx vitest run src/components/resources/ResourceCard.test.tsx` → FAIL.

- [ ] **Step 3: implementar `ResourceCard.tsx`**

```tsx
import { Youtube, BookOpen, FileText, ExternalLink } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { LearningResource, ResourceKind } from '@/types/resource'

const KIND_ICON: Record<ResourceKind, LucideIcon> = {
  video: Youtube,
  book: BookOpen,
  article: FileText,
  doc: FileText,
}

const KIND_LABEL: Record<ResourceKind, string> = {
  video: 'Video',
  book: 'Libro',
  article: 'Artículo',
  doc: 'Documentación',
}

export default function ResourceCard({ resource }: { resource: LearningResource }) {
  const Icon = KIND_ICON[resource.kind] ?? FileText
  return (
    <a
      href={resource.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex items-start gap-3 rounded-lg border border-border bg-card p-3
                 hover:border-primary/40 hover:bg-muted/40 transition-colors
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <Icon className="h-5 w-5 shrink-0 text-primary mt-0.5" aria-hidden="true" />
      <div className="flex-1 min-w-0">
        <p className="font-medium text-foreground flex items-center gap-1">
          <span className="truncate">{resource.title}</span>
          <ExternalLink className="h-3 w-3 shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100" aria-hidden="true" />
        </p>
        <p className="text-xs text-muted-foreground">
          {KIND_LABEL[resource.kind]}
          {resource.author ? ` · ${resource.author}` : ''}
        </p>
        {resource.description && (
          <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{resource.description}</p>
        )}
      </div>
    </a>
  )
}
```

- [ ] **Step 4: implementar `ResourceList.tsx`**

```tsx
import { BookOpen } from 'lucide-react'
import ResourceCard from './ResourceCard'
import { useResources } from '@/hooks/useResources'

interface Props {
  moduleId?: number
  topicId?: number
  title?: string
}

export default function ResourceList({ moduleId, topicId, title = 'Recursos para reforzar' }: Props) {
  const { data: resources } = useResources({ moduleId, topicId })
  if (!resources || resources.length === 0) return null
  return (
    <section aria-label={title} className="space-y-2">
      <h2 className="flex items-center gap-2 text-sm font-semibold text-foreground">
        <BookOpen className="h-4 w-4 text-primary" aria-hidden="true" />
        {title}
      </h2>
      <div className="grid gap-2 sm:grid-cols-2">
        {resources.map((r) => (
          <ResourceCard key={r.id} resource={r} />
        ))}
      </div>
    </section>
  )
}
```

- [ ] **Step 5:** `npx vitest run src/components/resources/ResourceCard.test.tsx` → 2 PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/resources/ResourceCard.tsx frontend/src/components/resources/ResourceList.tsx frontend/src/components/resources/ResourceCard.test.tsx
git commit -m "feat(resources): ResourceCard + ResourceList con test"
```

---

### Task 7: Montar `ResourceList` en Dashboard y Topic

**Files:**
- Modify: `frontend/src/pages/DashboardPage.tsx`
- Modify: `frontend/src/pages/TopicPage.tsx`

- [ ] **Step 1: Dashboard** — leer el archivo y, donde existan los módulos recomendados (`recommended_modules` del dashboard), montar `<ResourceList moduleId={...} title="Recursos recomendados" />` usando el `id` del PRIMER módulo recomendado, si existe. Si no hay módulos recomendados, no renderizar (el componente ya devuelve null si no hay datos, y el hook se deshabilita sin params). Insertar tras las recomendaciones, sin refactor.

```tsx
import ResourceList from '@/components/resources/ResourceList'
// ...donde haya datos del dashboard (data.recommended_modules):
{data?.recommended_modules?.[0] && (
  <ResourceList moduleId={data.recommended_modules[0].id} title="Recursos recomendados" />
)}
```
(Verificar el nombre real de la variable de datos del dashboard en el archivo — p.ej. `data`, `dashboard`. Usar el real.)

- [ ] **Step 2: Topic** — montar `<ResourceList topicId={topicId} />` cerca del final del contenido del tema (debajo del contenido/quiz, antes de la barra de navegación). Usar la misma variable `topicId` (`Number(id)`) ya presente; guardar con `!isNaN(topicId)`.

```tsx
import ResourceList from '@/components/resources/ResourceList'
// ...al final del contenido del tema:
{!isNaN(topicId) && <ResourceList topicId={topicId} />}
```

- [ ] **Step 3:** `npx tsc --noEmit && npx vitest run` (desde `frontend/`) → limpio + toda la suite pasa.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/DashboardPage.tsx frontend/src/pages/TopicPage.tsx
git commit -m "feat(resources): montar ResourceList en Dashboard y Topic"
```

---

### Task 8: Pestaña "Recursos" en AdminPage + métodos admin api

**Files:**
- Modify: `frontend/src/api/admin.ts` (agregar métodos CRUD de recursos + tipo)
- Create: `frontend/src/components/admin/ResourcesTab.tsx`
- Modify: `frontend/src/pages/AdminPage.tsx` (agregar pestaña)

- [ ] **Step 1: api admin** — en `frontend/src/api/admin.ts`, leer el patrón existente (p.ej. `listBank/createBankItem/...`) y agregar, importando `LearningResource` de `@/types/resource`:

```typescript
// en adminApi:
  listResources: (params?: { module_id?: number; topic_id?: number }) =>
    apiClient.get<LearningResource[]>('/admin/resources', { params }),
  createResource: (data: Partial<LearningResource>) =>
    apiClient.post<LearningResource>('/admin/resources', data),
  updateResource: (id: number, data: Partial<LearningResource>) =>
    apiClient.put<LearningResource>(`/admin/resources/${id}`, data),
  deleteResource: (id: number) =>
    apiClient.delete<void>(`/admin/resources/${id}`),
```
(Respetar el estilo real del objeto `adminApi` — si usa `export const adminApi = { ... }`, agregar las claves dentro; si re-exporta tipos, añadir el import de `LearningResource`.)

- [ ] **Step 2: ResourcesTab.tsx** — seguir el patrón de `BankTab.tsx` (filtro por módulo, tabla, crear vía prompts, toggle activo, editar título, eliminar con confirm). Columnas: Módulo/Tema · Tipo · Título · Estado · acciones. Crear con prompts: kind (video/book/article/doc), title, url, module_id (opcional), author (opcional).

```tsx
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Power, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'
import { adminApi } from '@/api/admin'
import type { LearningResource, ResourceKind } from '@/types/resource'
import { Button } from '@/components/ui/button'

const KINDS: ResourceKind[] = ['video', 'book', 'article', 'doc']

export default function ResourcesTab() {
  const queryClient = useQueryClient()
  const [moduleFilter, setModuleFilter] = useState<number | undefined>(undefined)

  const { data: modules } = useQuery({
    queryKey: ['admin', 'modules'],
    queryFn: () => adminApi.listModules().then((r) => r.data),
  })

  const { data: items, isLoading } = useQuery({
    queryKey: ['admin', 'resources', moduleFilter],
    queryFn: () =>
      adminApi.listResources({ module_id: moduleFilter }).then((r) => r.data),
  })

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ['admin', 'resources'] })

  const createItem = useMutation({
    mutationFn: adminApi.createResource,
    onSuccess: () => { toast.success('Recurso agregado'); invalidate() },
    onError: () => toast.error('Error al crear'),
  })
  const updateItem = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<LearningResource> }) =>
      adminApi.updateResource(id, data),
    onSuccess: () => { toast.success('Actualizado'); invalidate() },
  })
  const deleteItem = useMutation({
    mutationFn: adminApi.deleteResource,
    onSuccess: () => { toast.success('Eliminado'); invalidate() },
  })

  const handleCreate = () => {
    const kind = prompt('Tipo (video/book/article/doc):', 'video') as ResourceKind
    if (!KINDS.includes(kind)) return toast.error('Tipo inválido')
    const title = prompt('Título:')
    if (!title) return
    const url = prompt('URL (verifica que sea correcta):')
    if (!url) return
    const moduleStr = prompt('module_id (opcional, vacío = general):', moduleFilter ? String(moduleFilter) : '')
    const module_id = moduleStr ? Number(moduleStr) : undefined
    const author = prompt('Autor (opcional):') || undefined
    createItem.mutate({ kind, title, url, module_id, author })
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <select
          value={moduleFilter ?? ''}
          onChange={(e) => setModuleFilter(e.target.value ? Number(e.target.value) : undefined)}
          className="text-sm border border-border bg-background text-foreground rounded px-3 py-1.5"
        >
          <option value="">Todos los módulos</option>
          {modules?.map((m) => (
            <option key={m.id} value={m.id}>{m.order_index}. {m.title}</option>
          ))}
        </select>
        <Button onClick={handleCreate}><Plus className="w-4 h-4 mr-1" />Nuevo recurso</Button>
      </div>

      <p className="text-xs text-muted-foreground mb-3">
        Los recursos son curados manualmente. Verifica cada URL antes de publicarla — el sistema no genera enlaces automáticamente.
      </p>

      <div className="bg-card border border-border rounded-xl overflow-x-auto">
        {isLoading ? (
          <div className="p-8 text-center text-muted-foreground">Cargando...</div>
        ) : !items || items.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground text-sm">Sin recursos. Agrega videos o libros para reforzar el aprendizaje.</div>
        ) : (
          <table className="w-full text-sm min-w-[640px]">
            <thead className="bg-muted text-muted-foreground text-xs uppercase">
              <tr>
                <th className="px-4 py-3 text-left">Módulo</th>
                <th className="px-4 py-3 text-left">Tipo</th>
                <th className="px-4 py-3 text-left">Título</th>
                <th className="px-4 py-3 text-left">Estado</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-t border-border">
                  <td className="px-4 py-3 text-foreground">{item.module_id ? `M${item.module_id}` : '—'}</td>
                  <td className="px-4 py-3 text-foreground uppercase text-xs">{item.kind}</td>
                  <td className="px-4 py-3 max-w-md truncate text-foreground">
                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 hover:underline">
                      {item.title}<ExternalLink className="w-3 h-3" />
                    </a>
                  </td>
                  <td className="px-4 py-3 text-xs">
                    <span className={item.is_active ? 'text-success' : 'text-muted-foreground'}>
                      {item.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex gap-1 justify-end">
                      <Button size="sm" variant="ghost" onClick={() => updateItem.mutate({ id: item.id, data: { is_active: !item.is_active } })}>
                        <Power className="w-3 h-3" />
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => { if (confirm('¿Eliminar?')) deleteItem.mutate(item.id) }}>
                        <Trash2 className="w-3 h-3 text-destructive" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: AdminPage** — agregar la pestaña "Recursos":
  - Importar `ResourcesTab` y un icono (p.ej. `Library` de lucide).
  - Añadir `'resources'` al tipo `TabId`.
  - Añadir `{ id: 'resources', label: 'Recursos', icon: Library }` al arreglo `TABS`.
  - Añadir `{tab === 'resources' && <ResourcesTab />}` al render.

- [ ] **Step 4:** `npx tsc --noEmit && npx vitest run` → limpio + verde.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/admin.ts frontend/src/components/admin/ResourcesTab.tsx frontend/src/pages/AdminPage.tsx
git commit -m "feat(resources): pestana admin Recursos (CRUD)"
```

---

### Task 9: Documentación

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/matriz-trazabilidad-ISO25010.md`

- [ ] **Step 1: CLAUDE.md** — (a) en la sección "🔌 API REST" agregar bajo el subapartado `/tutor` (o cerca) un bloque `### /resources` con `GET /resources?module_id=&topic_id=` (estudiante) y notar el CRUD admin en `/admin/resources`. (b) En "Fases completadas", agregar bullet:

```
- **ACOMPAÑAMIENTO PROACTIVO (Fase 3) ✅** Banco de recursos curados `learning_resources` (migración 006) — videos/libros/artículos por módulo/tema. Endpoint estudiante `GET /resources`; CRUD admin `/admin/resources` + pestaña "Recursos" en AdminPage; `ResourceList` montado en Dashboard y Topic. Seed inicial con URLs marcadas para verificación humana. El LLM NUNCA genera recursos (regla "no inventa"). Cierra el pedido del jurado (links de libros/videos).
```

- [ ] **Step 2: matriz ISO** — agregar `RF-NEW-TUTOR-03`: "Banco de recursos de aprendizaje curados (videos/libros)" ↔ `/resources` + `/admin/resources` + `components/resources/*` ↔ Tests `test_router_resources.py` + `test_router_admin_resources.py` + `ResourceCard.test.tsx` ↔ "Pertinencia funcional / Operabilidad" ↔ implementado. Mismo formato de columnas; NO renumerar RF-01..33.

- [ ] **Step 3: guardian ISO** — `pytest tests/integration/test_iso25010.py -v` (desde `backend/`). Reconciliar si la fila nueva rompe algo (referenciar archivos de test existentes).

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md docs/matriz-trazabilidad-ISO25010.md
git commit -m "docs(resources): registrar Fase 3 banco de recursos y RF en matriz ISO"
```

---

## Verificación final de Fase 3

- [ ] `pytest -q` (backend) verde, sin regresiones; nuevos tests de resources pasan.
- [ ] `npx tsc --noEmit` y `npx vitest run` (frontend) verde.
- [ ] Migración 006 encadena tras 005 (revisión visual o `alembic upgrade head` si hay BD).
- [ ] Estudiante ve recursos por módulo (Dashboard) y por tema (Topic); admin hace CRUD en pestaña "Recursos".
- [ ] Seed marca claramente que las URLs son placeholders a verificar.
- [ ] CLAUDE.md + matriz ISO actualizados.

Al cerrar Fase 3, queda **Fase 4** (refuerzo en evaluaciones, reusa motor Fase 1) como última fase del acompañamiento proactivo.
