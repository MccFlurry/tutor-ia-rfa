"""
Integration conftest — provides an in-memory FastAPI client whose
`get_db`, `get_current_user`, and `get_redis` dependencies are replaced
with controllable mocks. No PostgreSQL / Redis / Ollama needed.

Each test pulls the `client` fixture and either:
- patches service functions to assert wiring, or
- attaches its own SQLAlchemy result side_effects to `mock_db`.
"""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.dependencies import get_current_user, get_redis
from app.main import app


def _build_user(role="student"):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="t@t.pe",
        full_name="Test User",
        hashed_password="x",
        role=role,
        is_active=True,
        avatar_url=None,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def fake_user():
    return _build_user()


@pytest.fixture
def fake_admin():
    return _build_user(role="admin")


@pytest.fixture
def mock_db():
    """Async DB mock — tests attach execute side_effects per call."""
    db = MagicMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def mock_redis_pipe():
    """Mock redis client supporting pipeline/get/setex usage."""
    client = MagicMock()
    client.get = AsyncMock(return_value=None)
    client.setex = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)

    pipe = MagicMock()
    pipe.incr = MagicMock(return_value=pipe)
    pipe.expire = MagicMock(return_value=pipe)
    pipe.execute = AsyncMock(return_value=[1, True])
    client.pipeline = MagicMock(return_value=pipe)
    return client


@pytest_asyncio.fixture
async def client(fake_user, mock_db, mock_redis_pipe):
    """ASGI test client with the three core deps overridden."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_redis] = lambda: mock_redis_pipe
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_client(fake_admin, mock_db, mock_redis_pipe):
    """ASGI test client authenticated as admin."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: fake_admin
    app.dependency_overrides[get_redis] = lambda: mock_redis_pipe
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def anon_client(mock_db, mock_redis_pipe):
    """ASGI test client with NO authenticated user — for /auth endpoints."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_redis] = lambda: mock_redis_pipe
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Result helpers — keep tests terse when stubbing execute() side effects.
# ---------------------------------------------------------------------------

def result_scalar(value):
    r = MagicMock()
    r.scalar = MagicMock(return_value=value)
    return r


def result_scalar_one_or_none(value):
    r = MagicMock()
    r.scalar_one_or_none = MagicMock(return_value=value)
    return r


def result_scalar_one(value):
    r = MagicMock()
    r.scalar_one = MagicMock(return_value=value)
    return r


def result_scalars_all(values):
    r = MagicMock()
    r.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=values)))
    return r


def result_rows(rows):
    """For result.first() / result.all() returning tuples (e.g. join queries)."""
    r = MagicMock()
    r.first = MagicMock(return_value=rows[0] if rows else None)
    r.all = MagicMock(return_value=rows)
    return r
