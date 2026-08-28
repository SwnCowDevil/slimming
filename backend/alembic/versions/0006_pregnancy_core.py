"""create pregnancy core tables

Revision ID: 0006_pregnancy_core
Revises: 0005_guidance
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0006_pregnancy_core"
down_revision: str | None = "0005_guidance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "product_mode",
            sa.String(24),
            nullable=False,
            server_default="legacy_slimming",
        ),
    )
    op.create_table(
        "pregnancy_episodes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("due_date_source", sa.String(32), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_pregnancy_episodes_user_id", "pregnancy_episodes", ["user_id"])
    op.create_index("ix_pregnancy_episodes_due_date", "pregnancy_episodes", ["due_date"])
    op.create_index("ix_pregnancy_episodes_status", "pregnancy_episodes", ["status"])
    op.create_table(
        "pregnancy_preferences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("pregnancy_episode_id", sa.String(36), sa.ForeignKey("pregnancy_episodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("height_cm", sa.Numeric(6, 2), nullable=False),
        sa.Column("pre_pregnancy_weight_kg", sa.Numeric(6, 2), nullable=True),
        sa.Column("activity_level", sa.String(20), nullable=False),
        sa.Column("dietary_preferences", sa.JSON(), nullable=False),
        sa.Column("allergens", sa.JSON(), nullable=False),
        sa.Column("avoidances", sa.JSON(), nullable=False),
        sa.Column("disliked_foods", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("pregnancy_episode_id", name="uq_pregnancy_preferences_episode"),
    )
    op.create_index("ix_pregnancy_preferences_episode", "pregnancy_preferences", ["pregnancy_episode_id"])
    op.create_table(
        "meal_schedules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("pregnancy_episode_id", sa.String(36), sa.ForeignKey("pregnancy_episodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("display_name", sa.String(40), nullable=False),
        sa.Column("scheduled_time", sa.String(5), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("pregnancy_episode_id", "code", name="uq_meal_schedule_episode_code"),
        sa.UniqueConstraint("pregnancy_episode_id", "position", name="uq_meal_schedule_episode_position"),
    )
    op.create_index("ix_meal_schedules_episode", "meal_schedules", ["pregnancy_episode_id"])
    op.create_table(
        "daily_wellbeing_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("pregnancy_episode_id", sa.String(36), sa.ForeignKey("pregnancy_episodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("feeling_codes", sa.JSON(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("pregnancy_episode_id", "log_date", name="uq_wellbeing_episode_date"),
    )
    op.create_index("ix_wellbeing_episode", "daily_wellbeing_logs", ["pregnancy_episode_id"])
    op.create_index("ix_wellbeing_user", "daily_wellbeing_logs", ["user_id"])
    op.create_index("ix_wellbeing_date", "daily_wellbeing_logs", ["log_date"])


def downgrade() -> None:
    op.drop_table("daily_wellbeing_logs")
    op.drop_table("meal_schedules")
    op.drop_table("pregnancy_preferences")
    op.drop_table("pregnancy_episodes")
    op.drop_column("users", "product_mode")
