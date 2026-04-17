import uuid
from datetime import datetime, timezone

from sqlalchemy import Integer, String, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, JSONB

from app.database import Base


class CodingChallenge(Base):
    __tablename__ = "coding_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    initial_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(50), default="kotlin")
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    hints: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Fase 6: AI personalization flags
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generated_for_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    student_level: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    topic = relationship("Topic", backref="coding_challenges")
    submissions = relationship("CodingSubmission", back_populates="challenge", cascade="all, delete-orphan")


class CodingSubmission(Base):
    __tablename__ = "coding_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    challenge_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("coding_challenges.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100
    feedback: Mapped[str] = mapped_column(Text, nullable=False)  # LLM evaluation in Markdown
    strengths: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    improvements: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    challenge = relationship("CodingChallenge", back_populates="submissions")
