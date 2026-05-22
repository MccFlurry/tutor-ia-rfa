"""
Unit tests para app/services/llm_service.py.
Cubre el parser robusto (_parse_llm_response): wrapper objeto, bare array,
markdown fences, validaciones de opciones e índice correcto. También
generate_quiz_questions con LLM mockeado para verificar parámetros + caminos
de error.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

from app.services import llm_service
from app.services.llm_service import (
    QuizGenerationError,
    _parse_llm_response,
    _truncate_content,
    generate_quiz_questions,
)


def _valid_question(idx=0):
    return {
        "question_text": f"Pregunta {idx}",
        "options": ["a", "b", "c", "d"],
        "correct_option_index": idx % 4,
        "explanation": "porque sí",
    }


class TestTruncateContent:
    def test_short_content_unchanged(self):
        s = "abc"
        assert _truncate_content(s, max_chars=100) == "abc"

    def test_long_content_truncated_with_marker(self):
        s = "x" * 5000
        out = _truncate_content(s, max_chars=100)
        assert out.startswith("x" * 100)
        assert "truncado" in out


class TestParseWrapperObject:
    def test_object_with_questions_key(self):
        raw = json.dumps({"questions": [_valid_question(0), _valid_question(1)]})
        q = _parse_llm_response(raw, num_questions=2)
        assert len(q) == 2

    def test_object_without_questions_key_raises(self):
        raw = json.dumps({"items": []})
        with pytest.raises(QuizGenerationError, match="sin la clave"):
            _parse_llm_response(raw, num_questions=1)


class TestParseBareArray:
    def test_bare_array_accepted(self):
        raw = json.dumps([_valid_question(0)])
        q = _parse_llm_response(raw, num_questions=1)
        assert len(q) == 1


class TestParseMarkdownFences:
    def test_strips_json_fence(self):
        raw = "```json\n" + json.dumps({"questions": [_valid_question(0)]}) + "\n```"
        q = _parse_llm_response(raw, num_questions=1)
        assert len(q) == 1

    def test_strips_plain_fence(self):
        raw = "```\n" + json.dumps([_valid_question(0)]) + "\n```"
        q = _parse_llm_response(raw, num_questions=1)
        assert len(q) == 1


class TestParseErrors:
    def test_invalid_json_raises(self):
        with pytest.raises(QuizGenerationError, match="JSON"):
            _parse_llm_response("{not json", num_questions=1)

    def test_recovers_array_substring_from_garbage(self):
        raw = "noise " + json.dumps([_valid_question(0)]) + " tail"
        q = _parse_llm_response(raw, num_questions=1)
        assert len(q) == 1

    def test_missing_question_text_raises(self):
        bad = _valid_question(0)
        bad["question_text"] = "  "
        raw = json.dumps([bad])
        with pytest.raises(QuizGenerationError, match="sin texto"):
            _parse_llm_response(raw, num_questions=1)

    def test_wrong_option_count_raises(self):
        bad = _valid_question(0)
        bad["options"] = ["a", "b", "c"]
        raw = json.dumps([bad])
        with pytest.raises(QuizGenerationError, match="4 opciones"):
            _parse_llm_response(raw, num_questions=1)

    def test_correct_index_out_of_range(self):
        bad = _valid_question(0)
        bad["correct_option_index"] = 7
        raw = json.dumps([bad])
        with pytest.raises(QuizGenerationError, match="correct_option_index"):
            _parse_llm_response(raw, num_questions=1)

    def test_empty_array_raises(self):
        with pytest.raises(QuizGenerationError):
            _parse_llm_response(json.dumps([]), num_questions=1)


class TestExplanationDefault:
    def test_blank_explanation_filled_with_default(self):
        q = _valid_question(0)
        q["explanation"] = "   "
        out = _parse_llm_response(json.dumps([q]), num_questions=1)
        assert out[0].explanation == "Sin explicación disponible."


class TestGenerateQuizQuestions:
    @pytest.mark.asyncio
    async def test_too_short_content_raises(self):
        with pytest.raises(QuizGenerationError, match="corto"):
            await generate_quiz_questions("hi")

    @pytest.mark.asyncio
    async def test_calls_ollama_with_format_json(self):
        captured = {}

        def fake_ctor(**kwargs):
            captured.update(kwargs)
            llm = MagicMock()
            payload = json.dumps({"questions": [_valid_question(0)]})
            llm.ainvoke = AsyncMock(return_value=SimpleNamespace(content=payload))
            return llm

        with patch.object(llm_service, "ChatOllama", side_effect=fake_ctor):
            out = await generate_quiz_questions("x" * 500, num_questions=1)
        assert len(out) == 1
        assert captured["format"] == "json"
        assert captured["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_unknown_level_falls_back_to_intermediate(self):
        # No exception means the LEVEL_GUIDANCE.get default kicked in.
        def fake_ctor(**kwargs):
            llm = MagicMock()
            payload = json.dumps({"questions": [_valid_question(0)]})
            llm.ainvoke = AsyncMock(return_value=SimpleNamespace(content=payload))
            return llm

        with patch.object(llm_service, "ChatOllama", side_effect=fake_ctor):
            out = await generate_quiz_questions("x" * 500, num_questions=1, student_level="alien")
        assert len(out) == 1

    @pytest.mark.asyncio
    async def test_ollama_failure_wraps_in_quiz_generation_error(self):
        def fake_ctor(**kwargs):
            llm = MagicMock()
            llm.ainvoke = AsyncMock(side_effect=RuntimeError("connection refused"))
            return llm

        with patch.object(llm_service, "ChatOllama", side_effect=fake_ctor):
            with pytest.raises(QuizGenerationError, match="No se pudo conectar"):
                await generate_quiz_questions("x" * 500, num_questions=1)
