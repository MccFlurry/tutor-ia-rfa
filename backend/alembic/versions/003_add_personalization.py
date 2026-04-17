"""Add personalization: user_levels, entry_assessment_sessions, entry_assessment_bank.

Revision ID: 003_personalization
Revises: 002_coding
Create Date: 2026-04-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003_personalization"
down_revision: Union[str, None] = "002_coding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_levels",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("entry_score", sa.Float, nullable=False),
        sa.Column("assessed_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("last_reassessed_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("history", postgresql.JSONB, nullable=True, server_default=sa.text("'[]'::jsonb")),
    )

    op.create_table(
        "entry_assessment_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("questions", postgresql.JSONB, nullable=False),
        sa.Column("answers", postgresql.JSONB, nullable=True),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("computed_level", sa.String(20), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    op.create_table(
        "entry_assessment_bank",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("module_id", sa.Integer, sa.ForeignKey("modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("options", postgresql.JSONB, nullable=False),
        sa.Column("correct_index", sa.Integer, nullable=False),
        sa.Column("difficulty", sa.String(20), server_default="medium", nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    op.create_index("idx_assessment_sessions_user", "entry_assessment_sessions", ["user_id"])
    op.create_index("idx_assessment_bank_module", "entry_assessment_bank", ["module_id"])
    op.create_index("idx_assessment_bank_difficulty", "entry_assessment_bank", ["difficulty"])
    op.create_index("idx_user_levels_level", "user_levels", ["level"])


def downgrade() -> None:
    op.drop_index("idx_user_levels_level")
    op.drop_index("idx_assessment_bank_difficulty")
    op.drop_index("idx_assessment_bank_module")
    op.drop_index("idx_assessment_sessions_user")
    op.drop_table("entry_assessment_bank")
    op.drop_table("entry_assessment_sessions")
    op.drop_table("user_levels")
