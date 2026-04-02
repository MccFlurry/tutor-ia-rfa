from datetime import datetime
from pydantic import BaseModel


class QuizQuestionResponse(BaseModel):
    id: str
    question_text: str
    options: list[str]

    model_config = {"from_attributes": True}


class QuizGenerateResponse(BaseModel):
    session_id: str
    questions: list[QuizQuestionResponse]


class QuizSubmitRequest(BaseModel):
    session_id: str
    answers: dict[str, int]  # {"q0": selected_index, "q1": selected_index, ...}


class QuizFeedbackItem(BaseModel):
    question_id: str
    question_text: str
    selected_index: int
    correct_index: int
    is_correct: bool
    explanation: str | None = None


class QuizSubmitResponse(BaseModel):
    score: float
    is_passed: bool
    feedback: list[QuizFeedbackItem]
    attempt_id: int


class QuizAttemptResponse(BaseModel):
    attempted_at: datetime
    score: float
    is_passed: bool

    model_config = {"from_attributes": True}
