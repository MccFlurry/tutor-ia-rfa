from datetime import datetime
from pydantic import BaseModel


class TopicBrief(BaseModel):
    id: int
    title: str
    order_index: int
    estimated_minutes: int
    has_quiz: bool
    status: str  # 'not_started' | 'in_progress' | 'completed'

    model_config = {"from_attributes": True}


class ModuleResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    order_index: int
    icon_name: str | None = None
    color_hex: str
    total_topics: int = 0
    completed_topics: int = 0
    progress_pct: float = 0.0
    is_locked: bool = False

    model_config = {"from_attributes": True}


class ModuleDetailResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    order_index: int
    icon_name: str | None = None
    color_hex: str
    total_topics: int = 0
    completed_topics: int = 0
    progress_pct: float = 0.0
    topics: list[TopicBrief] = []

    model_config = {"from_attributes": True}
