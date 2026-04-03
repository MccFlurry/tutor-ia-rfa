from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# --- Sessions ---

class ChatSessionCreate(BaseModel):
    """Body for creating a new chat session (empty — auto-generated title)."""
    pass


class ChatSessionResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    last_message_at: datetime

    model_config = {"from_attributes": True}


# --- Messages ---

class ChatSourceItem(BaseModel):
    content_preview: str
    document_name: str
    similarity: float


class ChatMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    message_id: UUID
    role: str
    content: str
    sources: list[ChatSourceItem] | None = None
    created_at: datetime


class ChatHistoryMessage(BaseModel):
    id: UUID
    role: str
    content: str
    sources: list[ChatSourceItem] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Misc ---

class MessageResponse(BaseModel):
    message: str
