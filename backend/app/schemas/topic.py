from datetime import datetime
from pydantic import BaseModel


class TopicModuleInfo(BaseModel):
    id: int
    title: str

    model_config = {"from_attributes": True}


class TopicProgressInfo(BaseModel):
    is_completed: bool = False
    time_spent_seconds: int = 0
    first_visited_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class TopicResponse(BaseModel):
    id: int
    title: str
    content_markdown: str
    video_url: str | None = None
    estimated_minutes: int
    has_quiz: bool
    order_index: int
    module: TopicModuleInfo
    progress_info: TopicProgressInfo | None = None

    model_config = {"from_attributes": True}


class TopicVisitResponse(BaseModel):
    message: str


class TopicCompleteResponse(BaseModel):
    message: str
    is_completed: bool


class TopicTimeRequest(BaseModel):
    seconds: int


class TopicTimeResponse(BaseModel):
    message: str
    total_seconds: int
