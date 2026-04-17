"""Admin schemas: assessment bank CRUD + user level overview."""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class AssessmentBankItemCreate(BaseModel):
    module_id: int
    question_text: str = Field(min_length=10)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    difficulty: str = Field(pattern="^(easy|medium|hard)$")


class AssessmentBankItemUpdate(BaseModel):
    question_text: str | None = None
    options: list[str] | None = None
    correct_index: int | None = Field(default=None, ge=0, le=3)
    difficulty: str | None = Field(default=None, pattern="^(easy|medium|hard)$")
    is_active: bool | None = None


class AssessmentBankItemResponse(BaseModel):
    id: int
    module_id: int
    question_text: str
    options: list[str]
    correct_index: int
    difficulty: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserLevelRow(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str
    level: str | None
    entry_score: float | None
    assessed_at: datetime | None
    last_reassessed_at: datetime | None


class AdminUserLevelOverride(BaseModel):
    level: str = Field(pattern="^(beginner|intermediate|advanced)$")
    reason: str = Field(min_length=3, max_length=255)
