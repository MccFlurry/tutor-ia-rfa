from pydantic import BaseModel


class ModuleProgressItem(BaseModel):
    id: int
    title: str
    pct: float
    completed: int
    total: int


class ProgressResponse(BaseModel):
    overall_pct: float
    total_time_seconds: int
    topics_completed: int
    quiz_avg_score: float | None = None
    modules: list[ModuleProgressItem] = []
