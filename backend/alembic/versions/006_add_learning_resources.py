"""Add learning_resources table (curated videos/books per module/topic).

Revision ID: 006_learning_resources
Revises: 005_ai_quiz_sessions
Create Date: 2026-05-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006_learning_resources"
down_revision: Union[str, None] = "005_ai_quiz_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "learning_resources",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "module_id", sa.Integer,
            sa.ForeignKey("modules.id", ondelete="CASCADE"), nullable=True,
        ),
        sa.Column(
            "topic_id", sa.Integer,
            sa.ForeignKey("topics.id", ondelete="CASCADE"), nullable=True,
        ),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"), nullable=True,
        ),
        sa.Column(
            "created_at", postgresql.TIMESTAMP(timezone=True),
            nullable=False, server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_resources_module", "learning_resources", ["module_id"])
    op.create_index("idx_resources_topic", "learning_resources", ["topic_id"])


def downgrade() -> None:
    op.drop_index("idx_resources_topic")
    op.drop_index("idx_resources_module")
    op.drop_table("learning_resources")
