"""
Unit tests for leveling_service · CRISP-DM classifier (rule-based v1).
Cubre: compute_level, umbrales, pesos módulo/dificultad, confianza.
"""

import pytest

from app.services.leveling_service import (
    compute_level,
    _level_from_score,
    LEVEL_THRESHOLDS,
    MODULE_WEIGHTS,
    DIFFICULTY_WEIGHTS,
)


class TestLevelFromScore:
    def test_zero_is_beginner(self):
        assert _level_from_score(0.0) == "beginner"

    def test_just_below_intermediate_threshold(self):
        # < 40 es beginner
        assert _level_from_score(LEVEL_THRESHOLDS["beginner_max"] - 0.01) == "beginner"

    def test_exactly_beginner_threshold_is_intermediate(self):
        # >= 40 cruza a intermediate
        assert _level_from_score(LEVEL_THRESHOLDS["beginner_max"]) == "intermediate"

    def test_mid_intermediate(self):
        assert _level_from_score(60.0) == "intermediate"

    def test_just_below_advanced_threshold(self):
        assert _level_from_score(LEVEL_THRESHOLDS["intermediate_max"] - 0.01) == "intermediate"

    def test_exactly_advanced_threshold(self):
        assert _level_from_score(LEVEL_THRESHOLDS["intermediate_max"]) == "advanced"

    def test_perfect_is_advanced(self):
        assert _level_from_score(100.0) == "advanced"


class TestWeights:
    def test_module_weights_increasing(self):
        # Módulos más avanzados pesan más
        assert MODULE_WEIGHTS[1] < MODULE_WEIGHTS[2]
        assert MODULE_WEIGHTS[4] < MODULE_WEIGHTS[5]
        assert MODULE_WEIGHTS[5] == 1.5

    def test_difficulty_weights_increasing(self):
        assert DIFFICULTY_WEIGHTS["easy"] < DIFFICULTY_WEIGHTS["medium"]
        assert DIFFICULTY_WEIGHTS["medium"] < DIFFICULTY_WEIGHTS["hard"]
        assert DIFFICULTY_WEIGHTS["hard"] == 2.0


class TestComputeLevel:
    def test_all_correct_is_advanced(self, sample_assessment_questions):
        answers = {q["id"]: q["correct_index"] for q in sample_assessment_questions}
        result = compute_level(sample_assessment_questions, answers)
        assert result.level == "advanced"
        assert result.score == 100.0
        assert 0.9 <= result.confidence <= 1.0

    def test_all_wrong_is_beginner(self, sample_assessment_questions):
        answers = {q["id"]: (q["correct_index"] + 1) % 4 for q in sample_assessment_questions}
        result = compute_level(sample_assessment_questions, answers)
        assert result.level == "beginner"
        assert result.score == 0.0

    def test_empty_answers_is_beginner(self, sample_assessment_questions):
        result = compute_level(sample_assessment_questions, {})
        assert result.level == "beginner"
        assert result.score == 0.0
        # No answered → low confidence on answer_rate side
        assert result.confidence < 1.0

    def test_module_breakdown_populated(self, sample_assessment_questions):
        answers = {q["id"]: q["correct_index"] for q in sample_assessment_questions}
        result = compute_level(sample_assessment_questions, answers)
        assert set(result.module_breakdown.keys()) == {1, 2, 3, 4, 5}
        for mid, stats in result.module_breakdown.items():
            assert stats["total"] >= 1
            assert stats["percentage"] == 100.0

    def test_hard_questions_weigh_more(self):
        """
        Dos estudiantes con mismo número de aciertos, pero uno acierta las hard.
        El que acertó las hard debe tener score mayor.
        """
        questions = [
            {"id": "q1", "correct_index": 0, "module_id": 3, "difficulty": "easy"},
            {"id": "q2", "correct_index": 0, "module_id": 3, "difficulty": "hard"},
        ]
        only_easy = compute_level(questions, {"q1": 0, "q2": 1})
        only_hard = compute_level(questions, {"q1": 1, "q2": 0})
        assert only_hard.score > only_easy.score

    def test_advanced_module_weighs_more(self):
        """M5 (peso 1.5) acertado vs M1 (peso 1.0) acertado → M5 da mejor score."""
        questions = [
            {"id": "q1", "correct_index": 0, "module_id": 1, "difficulty": "medium"},
            {"id": "q2", "correct_index": 0, "module_id": 5, "difficulty": "medium"},
        ]
        only_m1 = compute_level(questions, {"q1": 0, "q2": 1})
        only_m5 = compute_level(questions, {"q1": 1, "q2": 0})
        assert only_m5.score > only_m1.score

    def test_partial_coverage_lowers_confidence(self):
        # Solo 2 módulos cubiertos → confianza baja de cobertura
        questions = [
            {"id": "q1", "correct_index": 0, "module_id": 1, "difficulty": "easy"},
            {"id": "q2", "correct_index": 0, "module_id": 2, "difficulty": "easy"},
        ]
        result = compute_level(questions, {"q1": 0, "q2": 0})
        # coverage = 2/5 = 0.4, answer_rate = 1.0 → (0.4*0.5 + 1.0*0.5) = 0.70
        assert result.confidence == pytest.approx(0.7, abs=0.01)

    def test_score_is_rounded(self, sample_assessment_questions):
        # 2 decimales máximo
        answers = {"q1": 0, "q2": 1, "q3": 2}
        result = compute_level(sample_assessment_questions, answers)
        assert result.score == round(result.score, 2)
