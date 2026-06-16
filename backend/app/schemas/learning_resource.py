"""schemas/learning_resource.py — Recursos de aprendizaje curados."""
from typing import Literal

from pydantic import BaseModel, ConfigDict

ResourceKind = Literal["video", "book", "article", "doc"]


class LearningResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    module_id: int | None
    topic_id: int | None
    kind: str
    title: str
    url: str
    author: str | None
    description: str | None
    order_index: int
    is_active: bool


class LearningResourceCreate(BaseModel):
    module_id: int | None = None
    topic_id: int | None = None
    kind: ResourceKind
    title: str
    url: str
    author: str | None = None
    description: str | None = None
    order_index: int = 0


class LearningResourceUpdate(BaseModel):
    module_id: int | None = None
    topic_id: int | None = None
    kind: ResourceKind | None = None
    title: str | None = None
    url: str | None = None
    author: str | None = None
    description: str | None = None
    order_index: int | None = None
    is_active: bool | None = None


class RecommendedResource(LearningResourceResponse):
    """A curated resource plus the LLM's 1-line rationale (None in fallback)."""
    reason: str | None = None


class RecommendationResponse(BaseModel):
    ai_ranked: bool
    level: str
    recommendations: list[RecommendedResource]
