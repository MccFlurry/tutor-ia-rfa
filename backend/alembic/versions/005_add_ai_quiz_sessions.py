"""Persist AI-generated quiz sessions per user+topic.

Revision ID: 005_ai_quiz_sessions
Revises: 004_ai_challenge
Create Date: 2026-05-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005_ai_quiz_sessions"
down_revision: Union[str, None] = "004_ai_challenge"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_quiz_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "topic_id",
            sa.Integer,
            sa.ForeignKey("topics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("questions", postgresql.JSONB, nullable=False),
        sa.Column("student_level", sa.String(20), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="ai"),
        sa.Column(
            "is_submitted",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "submitted_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )

    # Only one active (not yet submitted) session per user+topic
    op.create_index(
        "uq_ai_quiz_active",
        "ai_quiz_sessions",
        ["user_id", "topic_id"],
        unique=True,
        postgresql_where=sa.text("is_submitted = false"),
    )
    op.create_index("idx_ai_quiz_user", "ai_quiz_sessions", ["user_id"])
    op.create_index("idx_ai_quiz_topic", "ai_quiz_sessions", ["topic_id"])


def downgrade() -> None:
    op.drop_index("idx_ai_quiz_topic")
    op.drop_index("idx_ai_quiz_user")
    op.drop_index("uq_ai_quiz_active")
    op.drop_table("ai_quiz_sessions")
