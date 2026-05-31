"""schemas/tutor.py — Nudges proactivos del tutor (deterministas, sin LLM)."""
from dataclasses import dataclass
from typing import Literal
from pydantic import BaseModel


class Nudge(BaseModel):
    id: str          # id estable de la regla, p.ej. "no_level"
    tone: Literal["info", "success", "warning", "encourage"]
    icon: str        # nombre de icono lucide (ej. "compass", "rocket", "flame")
    title: str
    message: str
    cta_label: str | None = None
    cta_route: str | None = None


class NudgeResponse(BaseModel):
    nudges: list[Nudge]


@dataclass
class StudentSnapshot:
    """Estado del estudiante ya resuelto desde BD; insumo puro de build_nudges."""
    has_level: bool
    level: str | None
    overall_pct: float
    last_quiz_passed: bool | None
    last_quiz_topic_title: str | None
    last_quiz_topic_id: int | None
    days_inactive: int | None
    near_complete_module_title: str | None
    near_complete_module_id: int | None
    streak_days: int = 0
