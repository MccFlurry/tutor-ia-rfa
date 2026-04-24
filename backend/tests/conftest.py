"""
conftest.py — Fixtures compartidos pytest.
- event_loop: loop asíncrono sesión-wide.
- mock_redis, mock_ollama: mocks reutilizables.
- sample_modules, sample_assessment_questions: datos de prueba.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock
from types import SimpleNamespace

import pytest
import pytest_asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Reemplaza el loop por-función default para compartir entre tests async."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    """Mock Redis client con get/setex/incr/expire/delete/pipeline/aclose."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.setex = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)
    client.incr = AsyncMock(return_value=1)
    client.expire = AsyncMock(return_value=True)
    client.aclose = AsyncMock(return_value=None)

    # Pipeline support
    pipe = AsyncMock()
    pipe.incr = MagicMock(return_value=pipe)
    pipe.expire = MagicMock(return_value=pipe)
    pipe.execute = AsyncMock(return_value=[1, True])
    client.pipeline = MagicMock(return_value=pipe)
    return client


@pytest.fixture
def mock_ollama_ok():
    """Mock ChatOllama.ainvoke devolviendo una respuesta con .content."""
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=SimpleNamespace(content='{"questions":[]}'))
    return llm


@pytest.fixture
def mock_ollama_timeout():
    """Mock ChatOllama.ainvoke que lanza TimeoutError."""
    llm = MagicMock()
    llm.ainvoke = AsyncMock(side_effect=TimeoutError("Ollama timeout"))
    return llm


@pytest.fixture
def sample_modules():
    """5 módulos con IDs y pesos del sistema."""
    return [
        SimpleNamespace(id=1, title="Fundamentos", order_index=1),
        SimpleNamespace(id=2, title="Lógica Kotlin", order_index=2),
        SimpleNamespace(id=3, title="Interfaces UI", order_index=3),
        SimpleNamespace(id=4, title="Componentes y Datos", order_index=4),
        SimpleNamespace(id=5, title="Funcionalidades Avanzadas", order_index=5),
    ]


@pytest.fixture
def sample_assessment_questions():
    """12 preguntas distribuidas M1-M5 con dificultad mixta."""
    return [
        {"id": "q1", "correct_index": 0, "module_id": 1, "difficulty": "easy"},
        {"id": "q2", "correct_index": 1, "module_id": 1, "difficulty": "medium"},
        {"id": "q3", "correct_index": 2, "module_id": 2, "difficulty": "easy"},
        {"id": "q4", "correct_index": 3, "module_id": 2, "difficulty": "medium"},
        {"id": "q5", "correct_index": 0, "module_id": 2, "difficulty": "hard"},
        {"id": "q6", "correct_index": 1, "module_id": 3, "difficulty": "easy"},
        {"id": "q7", "correct_index": 2, "module_id": 3, "difficulty": "medium"},
        {"id": "q8", "correct_index": 0, "module_id": 4, "difficulty": "medium"},
        {"id": "q9", "correct_index": 1, "module_id": 4, "difficulty": "hard"},
        {"id": "q10", "correct_index": 2, "module_id": 5, "difficulty": "easy"},
        {"id": "q11", "correct_index": 3, "module_id": 5, "difficulty": "medium"},
        {"id": "q12", "correct_index": 0, "module_id": 5, "difficulty": "hard"},
    ]
