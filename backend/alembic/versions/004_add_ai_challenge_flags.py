"""Add AI-generated-per-student flags to coding_challenges.

Revision ID: 004_ai_challenge
Revises: 003_personalization
Create Date: 2026-04-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004_ai_challenge"
down_revision: Union[str, None] = "003_personalization"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "coding_challenges",
        sa.Column("is_ai_generated", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "coding_challenges",
        sa.Column("generated_for_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
    )
    op.add_column(
        "coding_challenges",
        sa.Column("student_level", sa.String(20), nullable=True),
    )

    op.create_index(
        "idx_coding_challenges_user_topic",
        "coding_challenges",
        ["generated_for_user_id", "topic_id"],
    )
    op.create_index(
        "idx_coding_challenges_ai",
        "coding_challenges",
        ["is_ai_generated"],
    )


def downgrade() -> None:
    op.drop_index("idx_coding_challenges_ai")
    op.drop_index("idx_coding_challenges_user_topic")
    op.drop_column("coding_challenges", "student_level")
    op.drop_column("coding_challenges", "generated_for_user_id")
    op.drop_column("coding_challenges", "is_ai_generated")
