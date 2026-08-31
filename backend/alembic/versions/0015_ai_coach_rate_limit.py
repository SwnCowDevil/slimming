"""add atomic AI coach rate limit reservations

Revision ID: 0015_ai_coach_rate_limit
Revises: 0014_recipe_import_fingerprint
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0015_ai_coach_rate_limit"
down_revision: str | None = "0014_recipe_import_fingerprint"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_coach_rate_limit_reservations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scope", sa.String(8), nullable=False),
        sa.Column("subject_hash", sa.String(64), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "scope",
            "subject_hash",
            "window_start",
            "slot",
            name="uq_ai_coach_rate_limit_slot",
        ),
    )
    op.create_index(
        "ix_ai_coach_rate_limit_reservations_request_id",
        "ai_coach_rate_limit_reservations",
        ["request_id"],
    )
    op.create_index(
        "ix_ai_coach_rate_limit_reservations_created_at",
        "ai_coach_rate_limit_reservations",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ai_coach_rate_limit_reservations_created_at",
        table_name="ai_coach_rate_limit_reservations",
    )
    op.drop_index(
        "ix_ai_coach_rate_limit_reservations_request_id",
        table_name="ai_coach_rate_limit_reservations",
    )
    op.drop_table("ai_coach_rate_limit_reservations")
