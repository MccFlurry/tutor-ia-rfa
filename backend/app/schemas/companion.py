"""schemas/companion.py — Posición del estudiante + diagnóstico por módulo (Fase 5, sin LLM)."""
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from app.schemas.learning_resource import LearningResourceResponse


class TopicDiagnostic(BaseModel):
    topic_id: int
    title: str
    best_score: float | None
    attempts: int


class NextAction(BaseModel):
    kind: Literal["retry_quiz", "next_topic", "coding_challenge", "module"]
    label: str
    route: str


class ModuleDiagnostic(BaseModel):
    weak: list[TopicDiagnostic]       # repasar: score <60 o ≥2 intentos fallidos (y <80)
    practice: list[TopicDiagnostic]   # afianzar: mejor score en [60, 80)
    next_action: NextAction


class CompanionPosition(BaseModel):
    module_id: int
    module_title: str
    icon_name: str | None
    color_hex: str | None
    progress_pct: float
    topics_done: int
    topics_total: int
    course_completed: bool


class CompanionResponse(BaseModel):
    needs_assessment: bool
    position: CompanionPosition | None
    greeting: str
    diagnostic: ModuleDiagnostic | None
    resources: list[LearningResourceResponse]


@dataclass
class TopicStat:
    """Stats de un tema del módulo actual ya resueltos desde BD; insumo puro de build_diagnostic."""
    topic_id: int
    title: str
    order_index: int
    visited: bool
    completed: bool
    best_score: float | None   # mejor score de quiz (0-100), None si nunca intentó
    attempts: int
    failed_attempts: int
    has_coding_pending: bool   # hay desafío de catálogo sin aprobar (≥60) en este tema
