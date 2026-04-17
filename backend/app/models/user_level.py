import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, JSONB

from app.database import Base


class UserLevel(Base):
    __tablename__ = "user_levels"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    level: Mapped[str] = mapped_column(String(20), nullable=False)  # beginner | intermediate | advanced
    entry_score: Mapped[float] = mapped_column(Float, nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    last_reassessed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    history: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)

    user = relationship("User", back_populates="level_record")
