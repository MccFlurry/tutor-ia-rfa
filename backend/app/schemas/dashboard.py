"""Dashboard aggregation schemas."""
from datetime import datetime
from pydantic import BaseModel


class LastAccessedTopic(BaseModel):
    topic_id: int
    topic_title: str
    module_id: int
    module_title: str
    last_accessed_at: datetime
    is_completed: bool


class RecommendedModule(BaseModel):
    id: int
    title: str
    description: str | None
    icon_name: str | None
    color_hex: str
    progress_pct: float
    reason: str  # why recommended


class RecentAchievement(BaseModel):
    id: int
    name: str
    badge_emoji: str
    badge_color: str
    earned_at: datetime


class DashboardResponse(BaseModel):
    user_name: str
    user_level: str | None
    overall_progress_pct: float
    total_topics_completed: int
    total_topics: int
    last_accessed_topic: LastAccessedTopic | None
    recommended_modules: list[RecommendedModule]
    recent_achievements: list[RecentAchievement]
