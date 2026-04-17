"""Schemas for entry assessment (personalization)."""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class AssessmentQuestionResponse(BaseModel):
    id: str
    question_text: str
    options: list[str]
    module_id: int
    difficulty: str  # easy | medium | hard


class AssessmentStartResponse(BaseModel):
    session_id: uuid.UUID
    questions: list[AssessmentQuestionResponse]
    source: str  # "ai" | "bank"


class AssessmentSubmitRequest(BaseModel):
    session_id: uuid.UUID
    answers: dict[str, int]  # {qid: selected_index}


class ModuleScoreBreakdown(BaseModel):
    module_id: int
    module_title: str
    correct: int
    total: int
    percentage: float


class AssessmentSubmitResponse(BaseModel):
    level: str
    score: float
    confidence: float
    module_breakdown: list[ModuleScoreBreakdown]
    feedback: str
