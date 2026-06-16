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

import importlib
import re
from pathlib import Path

import pytest

# Nombres de módulo (no rutas de host): se localizan vía importlib, así el test
# corre igual desde el host, en el contenedor o en CI, sin depender del CWD.
SERVICES = [
    "app.services.llm_service",
    "app.services.challenge_generator_service",
    "app.services.code_eval_service",
    "app.services.rag_service",
]


@pytest.mark.parametrize("mod_name", SERVICES)
def test_chatollama_call_has_timeout(mod_name):
    mod = importlib.import_module(mod_name)
    source = Path(mod.__file__).read_text(encoding="utf-8")

    # Each ChatOllama(...) ctor block must contain timeout=settings.OLLAMA_TIMEOUT.
    pattern = re.compile(r"ChatOllama\((?P<body>.*?)\)", re.DOTALL)
    matches = list(pattern.finditer(source))

    assert matches, f"No ChatOllama(...) call found in {mod_name}"

    for m in matches:
        body = m.group("body")
        assert "timeout=settings.OLLAMA_TIMEOUT" in body, (
            f"ChatOllama(...) en {mod_name} no usa timeout=settings.OLLAMA_TIMEOUT — "
            f"riesgo: cortes silenciosos del LLM y caída a fallback. Cuerpo:\n{body}"
        )
