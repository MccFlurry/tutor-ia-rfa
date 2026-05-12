"""
Regression test: every ChatOllama instance in the backend MUST pass
`timeout=settings.OLLAMA_TIMEOUT`. Without this, langchain-ollama relies on
client-library defaults that frequently cut off generation mid-stream when the
qwen2.5:7b model is producing 1k+ tokens, which is the root cause of the AI
falling back to the catalogue on the first request.

Implementation: read each service file once and assert that any ChatOllama(...)
constructor call includes `timeout=settings.OLLAMA_TIMEOUT`. Cheap, deterministic,
no LLM required.
"""

import re
from pathlib import Path

import pytest

SERVICES = [
    "backend/app/services/llm_service.py",
    "backend/app/services/challenge_generator_service.py",
    "backend/app/services/code_eval_service.py",
    "backend/app/services/rag_service.py",
]


def _project_root() -> Path:
    # tests/unit/<this file>  →  project root is parents[3]
    return Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("rel_path", SERVICES)
def test_chatollama_call_has_timeout(rel_path):
    source = (_project_root() / rel_path).read_text(encoding="utf-8")

    # Each ChatOllama(...) ctor block must contain timeout=settings.OLLAMA_TIMEOUT.
    pattern = re.compile(r"ChatOllama\((?P<body>.*?)\)", re.DOTALL)
    matches = list(pattern.finditer(source))

    assert matches, f"No ChatOllama(...) call found in {rel_path}"

    for m in matches:
        body = m.group("body")
        assert "timeout=settings.OLLAMA_TIMEOUT" in body, (
            f"ChatOllama(...) en {rel_path} no usa timeout=settings.OLLAMA_TIMEOUT — "
            f"riesgo: cortes silenciosos del LLM y caída a fallback. Cuerpo:\n{body}"
        )
