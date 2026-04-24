"""
Unit tests for entry_assessment_service._parse_llm_response.
Valida robustez del parser frente a respuestas LLM con markdown, arrays desnudos, etc.
"""

import pytest

from app.services.entry_assessment_service import (
    _parse_llm_response,
    AssessmentGenerationError,
)

VALID_IDS = {1, 2, 3, 4, 5}


def _valid_question(module_id=1, difficulty="easy"):
    return {
        "question_text": "¿Qué es una Activity?",
        "options": ["A", "B", "C", "D"],
        "correct_index": 0,
        "module_id": module_id,
        "difficulty": difficulty,
    }


def _bulk_valid(n=10):
    return [_valid_question(module_id=(i % 5) + 1) for i in range(n)]


class TestParserObjectWrapper:
    def test_accepts_wrapper_with_questions(self):
        import json
        payload = json.dumps({"questions": _bulk_valid(6)})
        result = _parse_llm_response(payload, VALID_IDS)
        assert len(result) == 6

    def test_rejects_wrapper_without_questions_key(self):
        import json
        payload = json.dumps({"items": _bulk_valid(6)})
        with pytest.raises(AssessmentGenerationError):
            _parse_llm_response(payload, VALID_IDS)


class TestParserBareArray:
    def test_accepts_bare_array(self):
        import json
        payload = json.dumps(_bulk_valid(5))
        result = _parse_llm_response(payload, VALID_IDS)
        assert len(result) == 5


class TestParserMarkdownFences:
    def test_strips_json_markdown_fences(self):
        import json
        payload = "```json\n" + json.dumps({"questions": _bulk_valid(5)}) + "\n```"
        result = _parse_llm_response(payload, VALID_IDS)
        assert len(result) == 5

    def test_strips_plain_markdown_fences(self):
        import json
        payload = "```\n" + json.dumps({"questions": _bulk_valid(5)}) + "\n```"
        result = _parse_llm_response(payload, VALID_IDS)
        assert len(result) == 5


class TestParserValidation:
    def test_skips_questions_with_wrong_option_count(self):
        import json
        bad = _valid_question()
        bad["options"] = ["A", "B"]  # solo 2 opciones
        payload = json.dumps({"questions": [bad] + _bulk_valid(5)})
        result = _parse_llm_response(payload, VALID_IDS)
        assert len(result) == 5  # descarta la mala

    def test_skips_invalid_correct_index(self):
        import json
        bad = _valid_question()
        bad["correct_index"] = 9  # fuera de rango
        payload = json.dumps({"questions": [bad] + _bulk_valid(5)})
        result = _parse_llm_response(payload, VALID_IDS)
        assert len(result) == 5

    def test_skips_invalid_module_id(self):
        import json
        bad = _valid_question()
        bad["module_id"] = 99  # inexistente
        payload = json.dumps({"questions": [bad] + _bulk_valid(5)})
        result = _parse_llm_response(payload, VALID_IDS)
        assert len(result) == 5

    def test_defaults_invalid_difficulty_to_medium(self):
        import json
        q = _valid_question(difficulty="super-extreme")
        payload = json.dumps({"questions": [q] * 5})
        result = _parse_llm_response(payload, VALID_IDS)
        assert all(r.difficulty == "medium" for r in result)

    def test_raises_when_fewer_than_5_valid(self):
        import json
        payload = json.dumps({"questions": _bulk_valid(3)})
        with pytest.raises(AssessmentGenerationError):
            _parse_llm_response(payload, VALID_IDS)


class TestParserMalformedInput:
    def test_raises_on_invalid_json(self):
        with pytest.raises(AssessmentGenerationError):
            _parse_llm_response("not json at all }{", VALID_IDS)

    def test_raises_on_empty_list(self):
        with pytest.raises(AssessmentGenerationError):
            _parse_llm_response("[]", VALID_IDS)
