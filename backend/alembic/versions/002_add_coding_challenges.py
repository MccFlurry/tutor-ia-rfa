"""Add coding challenges and submissions tables.

Revision ID: 002_coding
Revises: 001_initial
Create Date: 2026-04-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002_coding"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "coding_challenges",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("topic_id", sa.Integer, sa.ForeignKey("topics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("initial_code", sa.Text, nullable=True),
        sa.Column("language", sa.String(50), server_default="kotlin"),
        sa.Column("difficulty", sa.String(20), server_default="medium"),
        sa.Column("hints", sa.Text, nullable=True),
        sa.Column("solution_code", sa.Text, nullable=True),
        sa.Column("order_index", sa.Integer, server_default="0"),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    op.create_table(
        "coding_submissions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("challenge_id", sa.Integer, sa.ForeignKey("coding_challenges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.Text, nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("feedback", sa.Text, nullable=False),
        sa.Column("strengths", postgresql.JSONB, nullable=True),
        sa.Column("improvements", postgresql.JSONB, nullable=True),
        sa.Column("submitted_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    op.create_index("idx_coding_challenges_topic", "coding_challenges", ["topic_id"])
    op.create_index("idx_coding_submissions_user", "coding_submissions", ["user_id"])
    op.create_index("idx_coding_submissions_challenge", "coding_submissions", ["challenge_id"])


def downgrade() -> None:
    op.drop_index("idx_coding_submissions_challenge")
    op.drop_index("idx_coding_submissions_user")
    op.drop_index("idx_coding_challenges_topic")
    op.drop_table("coding_submissions")
    op.drop_table("coding_challenges")
