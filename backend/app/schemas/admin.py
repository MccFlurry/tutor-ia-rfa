"""Admin schemas for content CRUD, documents, users, AI challenge generation."""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field


# ---------- Modules ----------

class ModuleCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    order_index: int = Field(ge=1)
    icon_name: str | None = None
    color_hex: str = Field(default="#3b82f6", pattern="^#[0-9a-fA-F]{6}$")
    is_active: bool = True


class ModuleUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    order_index: int | None = None
    icon_name: str | None = None
    color_hex: str | None = None
    is_active: bool | None = None


class ModuleAdminResponse(BaseModel):
    id: int
    title: str
    description: str | None
    order_index: int
    icon_name: str | None
    color_hex: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Topics ----------

class TopicCreateRequest(BaseModel):
    module_id: int
    title: str = Field(min_length=2, max_length=255)
    content: str = ""
    video_url: str | None = None
    order_index: int = Field(ge=1)
    estimated_minutes: int = 10
    has_quiz: bool = False
    is_active: bool = True


class TopicUpdateRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    video_url: str | None = None
    order_index: int | None = None
    estimated_minutes: int | None = None
    has_quiz: bool | None = None
    is_active: bool | None = None


class TopicAdminResponse(BaseModel):
    id: int
    module_id: int
    title: str
    content: str
    video_url: str | None
    order_index: int
    estimated_minutes: int
    has_quiz: bool
    is_active: bool

    model_config = {"from_attributes": True}


# ---------- Quiz questions (static bank) ----------

class QuizQuestionCreateRequest(BaseModel):
    topic_id: int
    question_text: str = Field(min_length=5)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_option_index: int = Field(ge=0, le=3)
    explanation: str | None = None
    order_index: int = 0


class QuizQuestionUpdateRequest(BaseModel):
    question_text: str | None = None
    options: list[str] | None = None
    correct_option_index: int | None = Field(default=None, ge=0, le=3)
    explanation: str | None = None
    order_index: int | None = None


class QuizQuestionAdminResponse(BaseModel):
    id: int
    topic_id: int
    question_text: str
    options: list[str]
    correct_option_index: int
    explanation: str | None
    order_index: int

    model_config = {"from_attributes": True}


# ---------- Coding challenges ----------

class CodingChallengeCreateRequest(BaseModel):
    topic_id: int
    title: str = Field(min_length=2, max_length=255)
    description: str
    initial_code: str | None = None
    language: str = "kotlin"
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    hints: str | None = None
    solution_code: str | None = None
    order_index: int = 0


class CodingChallengeUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    initial_code: str | None = None
    language: str | None = None
    difficulty: str | None = Field(default=None, pattern="^(easy|medium|hard)$")
    hints: str | None = None
    solution_code: str | None = None
    order_index: int | None = None


class CodingChallengeAdminResponse(BaseModel):
    id: int
    topic_id: int
    title: str
    description: str
    initial_code: str | None
    language: str
    difficulty: str
    hints: str | None
    solution_code: str | None
    order_index: int

    model_config = {"from_attributes": True}


class GenerateChallengeRequest(BaseModel):
    topic_id: int
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    target_level: str = Field(default="intermediate", pattern="^(beginner|intermediate|advanced)$")


class GeneratedChallengePreview(BaseModel):
    title: str
    description: str
    hints: str
    solution_code: str
    difficulty: str
    language: str


# ---------- Documents (RAG corpus) ----------

class DocumentAdminResponse(BaseModel):
    id: uuid.UUID
    original_filename: str
    file_size_bytes: int | None
    mime_type: str | None
    status: str
    error_message: str | None
    chunk_count: int
    uploaded_by: uuid.UUID | None
    created_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}


# ---------- Users ----------

class UserAdminRow(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    level: str | None = None

    model_config = {"from_attributes": True}


class UserAdminUpdate(BaseModel):
    role: str | None = Field(default=None, pattern="^(student|admin)$")
    is_active: bool | None = None
