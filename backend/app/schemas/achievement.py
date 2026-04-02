from datetime import datetime
from pydantic import BaseModel


class AchievementResponse(BaseModel):
    id: int
    name: str
    description: str
    badge_emoji: str
    badge_color: str
    is_earned: bool = False
    earned_at: datetime | None = None

    model_config = {"from_attributes": True}
