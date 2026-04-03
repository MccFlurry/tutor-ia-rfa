from datetime import datetime

from pydantic import BaseModel, Field


class CodingChallengeResponse(BaseModel):
    id: int
    topic_id: int
    title: str
    description: str
    initial_code: str | None
    language: str
    difficulty: str
    hints: str | None
    order_index: int

    model_config = {"from_attributes": True}


class CodingSubmitRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=10000)


class CodingEvaluationResponse(BaseModel):
    submission_id: int
    score: float
    feedback: str
    strengths: list[str] | None
    improvements: list[str] | None


class CodingSubmissionHistory(BaseModel):
    id: int
    code: str
    score: float
    feedback: str
    strengths: list[str] | None
    improvements: list[str] | None
    submitted_at: datetime

    model_config = {"from_attributes": True}


class TopicChallengesResponse(BaseModel):
    topic_id: int
    challenges: list[CodingChallengeResponse]
    has_challenges: bool
