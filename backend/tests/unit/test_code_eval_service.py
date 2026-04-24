"""
Unit tests para code_eval_service._parse_evaluation.
Validan que el parser maneje correctamente respuestas LLM malformadas
y normalice score, feedback, strengths, improvements.
"""

import json

from app.services.code_eval_service import _parse_evaluation


def _valid_eval_payload(score=85):
    return {
        "score": score,
        "feedback": "## Evaluación\n\nBuen trabajo en general.",
        "strengths": ["Código limpio", "Uso correcto de val/var"],
        "improvements": ["Añadir documentación"],
    }


class TestParseEvaluation:
    def test_accepts_well_formed_object(self):
        raw = json.dumps(_valid_eval_payload())
        parsed = _parse_evaluation(raw)
        assert parsed["score"] == 85
        assert "feedback" in parsed
        assert len(parsed["strengths"]) == 2
        assert len(parsed["improvements"]) == 1

    def test_strips_json_markdown_fences(self):
        raw = "```json\n" + json.dumps(_valid_eval_payload(70)) + "\n```"
        parsed = _parse_evaluation(raw)
        assert parsed["score"] == 70

    def test_strips_plain_markdown_fences(self):
        raw = "```\n" + json.dumps(_valid_eval_payload(50)) + "\n```"
        parsed = _parse_evaluation(raw)
        assert parsed["score"] == 50

    def test_clamps_score_above_100(self):
        raw = json.dumps({**_valid_eval_payload(), "score": 150})
        parsed = _parse_evaluation(raw)
        assert parsed["score"] == 100

    def test_clamps_negative_score(self):
        raw = json.dumps({**_valid_eval_payload(), "score": -10})
        parsed = _parse_evaluation(raw)
        assert parsed["score"] == 0

    def test_missing_fields_use_defaults(self):
        raw = json.dumps({"score": 60, "feedback": "Texto"})
        parsed = _parse_evaluation(raw)
        assert parsed["score"] == 60
        assert parsed["strengths"] == []
        assert parsed["improvements"] == []

    def test_invalid_json_returns_fallback_dict(self):
        parsed = _parse_evaluation("this is not JSON at all }}}{{{")
        assert parsed["score"] == 0
        assert "No se pudo evaluar" in parsed["feedback"]
        assert len(parsed["improvements"]) >= 1

    def test_non_list_strengths_coerced_to_empty(self):
        raw = json.dumps({**_valid_eval_payload(), "strengths": "una sola string"})
        parsed = _parse_evaluation(raw)
        assert parsed["strengths"] == []

    def test_strengths_truncated_to_max_5(self):
        raw = json.dumps({**_valid_eval_payload(), "strengths": [f"s{i}" for i in range(10)]})
        parsed = _parse_evaluation(raw)
        assert len(parsed["strengths"]) == 5

    def test_non_numeric_score_becomes_zero(self):
        raw = json.dumps({**_valid_eval_payload(), "score": "high"})
        parsed = _parse_evaluation(raw)
        assert parsed["score"] == 0
