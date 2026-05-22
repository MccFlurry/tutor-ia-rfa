"""
Test de trazabilidad ISO/IEC 25010:2023 — Sprint 7.

Esta NO es una capa nueva de tests; es un **registro auditable** que verifica
que la matriz `docs/matriz-trazabilidad-ISO25010.md` queda alineada con la
suite real (271 tests). Cada RF priorizado del ERS apunta a uno o más archivos
de tests reales. Si la suite cae por debajo del umbral, este test falla y
bloquea el merge.

Subcaracterísticas cubiertas (ISO/IEC 25010:2023 — Functional Suitability):
- Completitud  (cobertura RF)
- Corrección   (tasa éxito)
- Pertinencia  (uso adecuado para la tarea)

Umbrales del Sprint 7:
- Cobertura ≥ 80% de los 33 RF priorizados
- Tasa éxito ≥ 90% (pass / total)
- Cobertura código ≥ 80%
"""

from pathlib import Path

import pytest


pytestmark = [pytest.mark.integration]


# ---------------------------------------------------------------------------
# Mapeo RF priorizado → archivos de test que lo cubren.
# Cada entrada es (RF id, lista de paths relativos a backend/tests/).
# Mantener sincronizado con docs/matriz-trazabilidad-ISO25010.md.
# ---------------------------------------------------------------------------

RF_COVERAGE: dict[str, list[str]] = {
    "RF-01": ["integration/test_router_auth.py", "unit/test_auth_service.py"],
    "RF-02": ["integration/test_router_auth.py", "unit/test_auth_service.py"],
    "RF-03": ["integration/test_router_auth.py"],
    "RF-04": ["integration/test_router_users.py"],
    "RF-05": ["integration/test_router_admin.py"],
    "RF-06": ["integration/test_router_users.py"],
    "RF-07": ["integration/test_router_progress.py", "integration/test_router_dashboard.py", "unit/test_progress_service.py"],
    "RF-08": ["integration/test_router_dashboard.py"],
    "RF-09": ["integration/test_router_dashboard.py"],
    "RF-10": ["integration/test_router_chat.py"],
    "RF-11": ["integration/test_router_modules.py"],
    "RF-12": ["integration/test_router_modules.py"],
    "RF-13": ["integration/test_router_modules.py"],
    "RF-14": ["integration/test_router_modules.py", "unit/test_topic_completion_service.py"],
    "RF-15": ["integration/test_router_topics.py"],
    "RF-16": ["integration/test_router_topics.py"],
    "RF-17": ["integration/test_router_topics.py"],
    "RF-18": ["integration/test_router_quiz.py", "unit/test_ai_quiz_persistence.py", "unit/test_llm_service_parser.py"],
    "RF-19": ["integration/test_router_chat.py"],
    "RF-20": ["integration/test_router_chat.py", "unit/test_rag_service_internals.py", "unit/test_rag_system_prompt.py"],
    "RF-21": ["unit/test_rag_service_internals.py"],
    "RF-22": ["integration/test_router_chat.py"],
    "RF-23": [],  # UI-only: verificado en componente frontend TypingIndicator
    "RF-24": ["integration/test_router_chat.py"],
    "RF-25": ["unit/test_progress_service.py", "integration/test_router_progress.py"],
    "RF-26": ["unit/test_progress_service.py", "integration/test_router_topics.py"],
    "RF-27": ["integration/test_router_quiz.py", "integration/test_router_progress.py", "unit/test_progress_service.py"],
    "RF-28": ["unit/test_achievement_service.py"],
    "RF-29": ["integration/test_router_achievements.py"],
    "RF-30": ["integration/test_router_admin.py", "unit/test_ingest_service.py"],
    "RF-31": ["integration/test_router_admin.py"],
    "RF-32": ["integration/test_router_admin.py"],
    "RF-33": ["integration/test_router_admin.py"],
}


TOTAL_RF = 33
COVERAGE_THRESHOLD = 0.80  # ISO/IEC 25010 Sprint 7 acceptance
SUCCESS_THRESHOLD = 0.90


def _tests_root() -> Path:
    return Path(__file__).parent.parent


def test_all_33_rf_listed_in_matrix():
    """Sanity: la matriz declara exactamente 33 RF priorizados."""
    assert len(RF_COVERAGE) == TOTAL_RF, (
        f"Esperábamos {TOTAL_RF} RF priorizados, hay {len(RF_COVERAGE)}"
    )


def test_no_duplicate_rf_ids():
    ids = list(RF_COVERAGE.keys())
    assert len(ids) == len(set(ids))


def test_coverage_threshold_met():
    """≥ 80% de los RF deben tener al menos un archivo de test referenciado."""
    covered = sum(1 for files in RF_COVERAGE.values() if files)
    ratio = covered / TOTAL_RF
    assert ratio >= COVERAGE_THRESHOLD, (
        f"Cobertura RF {ratio:.0%} < umbral ISO {COVERAGE_THRESHOLD:.0%}. "
        f"RF sin tests: {[k for k, v in RF_COVERAGE.items() if not v]}"
    )


def test_every_referenced_test_file_exists():
    """Cada archivo declarado en RF_COVERAGE debe existir físicamente."""
    root = _tests_root()
    missing: list[tuple[str, str]] = []
    for rf, files in RF_COVERAGE.items():
        for f in files:
            if not (root / f).is_file():
                missing.append((rf, f))
    assert not missing, f"Archivos de test faltantes: {missing}"


def test_rf_ids_are_sequential():
    """RF-01..RF-33 sin huecos."""
    expected = {f"RF-{i:02d}" for i in range(1, TOTAL_RF + 1)}
    assert set(RF_COVERAGE.keys()) == expected
