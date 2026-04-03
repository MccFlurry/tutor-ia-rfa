"""
routers/chat.py — Tutor IA conversacional con RAG.
CRUD de sesiones + envío de mensajes con pipeline RAG + rate limiting.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_user, get_redis
from app.config import settings
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import (
    ChatSessionResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistoryMessage,
    MessageResponse,
)
from app.services.rag_service import query_rag
from app.services.achievement_service import check_and_grant_achievements
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["chat"])


# ----------------------------------------------------------------
# Rate limiting helper (Redis-based, per user)
# ----------------------------------------------------------------

async def _check_rate_limit(user_id: uuid.UUID, redis_client) -> int:
    """
    Check if user has exceeded chat rate limit.
    Returns remaining messages this hour.
    Raises 429 if limit exceeded.
    """
    key = f"chat_rate:{user_id}"
    current = await redis_client.get(key)

    if current is not None and int(current) >= settings.CHAT_RATE_LIMIT_PER_HOUR:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Has alcanzado el límite de {settings.CHAT_RATE_LIMIT_PER_HOUR} consultas por hora. Intenta de nuevo más tarde.",
        )

    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, 3600)  # TTL 1 hour
    results = await pipe.execute()
    count = results[0]

    return settings.CHAT_RATE_LIMIT_PER_HOUR - count


async def _get_remaining_messages(user_id: uuid.UUID, redis_client) -> int:
    """Get remaining messages this hour without incrementing."""
    key = f"chat_rate:{user_id}"
    current = await redis_client.get(key)
    used = int(current) if current else 0
    return max(0, settings.CHAT_RATE_LIMIT_PER_HOUR - used)


# ----------------------------------------------------------------
# Sessions
# ----------------------------------------------------------------

@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all chat sessions for the current user, most recent first."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.last_message_at.desc())
    )
    sessions = result.scalars().all()
    return [ChatSessionResponse.model_validate(s) for s in sessions]


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat session."""
    session = ChatSession(
        id=uuid.uuid4(),
        user_id=current_user.id,
        title="Nueva conversación",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    logger.info(f"Chat session creada: {session.id} por usuario {current_user.id}")
    return ChatSessionResponse.model_validate(session)


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def delete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a chat session and all its messages."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada")

    await db.delete(session)
    await db.commit()

    return MessageResponse(message="Sesión eliminada correctamente")


# ----------------------------------------------------------------
# Messages
# ----------------------------------------------------------------

@router.get("/sessions/{session_id}/messages", response_model=list[ChatHistoryMessage])
async def get_messages(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages in a chat session."""
    # Verify session belongs to user
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    if not session_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()

    return [
        ChatHistoryMessage(
            id=m.id,
            role=m.role,
            content=m.content,
            sources=m.sources,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.post("/sessions/{session_id}/message", response_model=ChatMessageResponse)
async def send_message(
    session_id: uuid.UUID,
    body: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """
    Send a message to the tutor IA.
    Executes the RAG pipeline and returns the assistant's response with sources.
    """
    # Verify session belongs to user
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada")

    # Check rate limit
    remaining = await _check_rate_limit(current_user.id, redis_client)

    # Save user message
    now = datetime.now(timezone.utc)
    user_msg = ChatMessage(
        id=uuid.uuid4(),
        session_id=session_id,
        user_id=current_user.id,
        role="user",
        content=body.content,
        created_at=now,
    )
    db.add(user_msg)

    # Get conversation history for RAG context
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    history_messages = history_result.scalars().all()
    session_history = [
        {"role": m.role, "content": m.content} for m in history_messages
    ]
    # Add the current user message to history
    session_history.append({"role": "user", "content": body.content})

    # Execute RAG pipeline
    try:
        rag_result = await query_rag(
            question=body.content,
            session_history=session_history,
            db=db,
            redis_client=redis_client,
        )
    except Exception as e:
        logger.error(f"Error en RAG pipeline: {e}")
        rag_result = {
            "content": "Lo siento, el tutor IA no está disponible en este momento. "
                       "Por favor, intenta de nuevo en unos minutos.",
            "sources": [],
        }

    # Save assistant message
    assistant_msg = ChatMessage(
        id=uuid.uuid4(),
        session_id=session_id,
        user_id=current_user.id,
        role="assistant",
        content=rag_result["content"],
        sources=rag_result["sources"] if rag_result["sources"] else None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(assistant_msg)

    # Update session title from first user message
    msg_count = await db.execute(
        select(func.count()).select_from(ChatMessage).where(
            ChatMessage.session_id == session_id,
            ChatMessage.role == "user",
        )
    )
    user_msg_count = msg_count.scalar()
    if user_msg_count <= 1:
        # First message — set session title
        session.title = body.content[:80] + ("..." if len(body.content) > 80 else "")

    session.last_message_at = datetime.now(timezone.utc)

    # Check chat_messages achievement
    await check_and_grant_achievements(current_user.id, db)

    await db.commit()

    return ChatMessageResponse(
        message_id=assistant_msg.id,
        role="assistant",
        content=rag_result["content"],
        sources=rag_result["sources"] if rag_result["sources"] else None,
        created_at=assistant_msg.created_at,
    )


@router.get("/remaining", response_model=dict)
async def get_remaining(
    current_user: User = Depends(get_current_user),
    redis_client=Depends(get_redis),
):
    """Get remaining chat messages for this hour."""
    remaining = await _get_remaining_messages(current_user.id, redis_client)
    return {
        "remaining": remaining,
        "limit": settings.CHAT_RATE_LIMIT_PER_HOUR,
    }
