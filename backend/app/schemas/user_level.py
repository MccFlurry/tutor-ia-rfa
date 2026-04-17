"""Schemas for user level + reassessment."""
from datetime import datetime
from pydantic import BaseModel


class LevelHistoryEntry(BaseModel):
    level: str
    score: float
    changed_at: datetime
    reason: str  # "entry" | "reassess_up" | "reassess_down" | "admin_override"


class UserLevelResponse(BaseModel):
    level: str | None
    entry_score: float | None
    assessed_at: datetime | None
    last_reassessed_at: datetime | None
    history: list[LevelHistoryEntry] = []

    model_config = {"from_attributes": True}


class ReassessmentProposal(BaseModel):
    should_reassess: bool
    direction: str | None = None  # "up" | "down"
    current_level: str | None = None
    proposed_level: str | None = None
    reason: str | None = None


class ReassessmentConfirmRequest(BaseModel):
    accept: bool  # true → apply proposed level, false → dismiss
