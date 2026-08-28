"""create daily meal plans and family tasks

Revision ID: 0009_meal_plans
Revises: 0008_family_collaboration
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0009_meal_plans"
down_revision: str | None = "0008_family_collaboration"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "meal_plan_days",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "pregnancy_episode_id",
            sa.String(36),
            sa.ForeignKey("pregnancy_episodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subject_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("plan_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("rule_version", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "pregnancy_episode_id", "plan_date", name="uq_meal_plan_episode_date"
        ),
    )
    op.create_index("ix_meal_plan_days_episode", "meal_plan_days", ["pregnancy_episode_id"])
    op.create_index("ix_meal_plan_days_subject", "meal_plan_days", ["subject_user_id"])
    op.create_index("ix_meal_plan_days_date", "meal_plan_days", ["plan_date"])

    op.create_table(
        "meal_plan_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "meal_plan_day_id",
            sa.String(36),
            sa.ForeignKey("meal_plan_days.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "meal_schedule_id",
            sa.String(36),
            sa.ForeignKey("meal_schedules.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("meal_name_snapshot", sa.String(40), nullable=False),
        sa.Column("scheduled_time_snapshot", sa.String(5), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "recipe_id",
            sa.String(64),
            sa.ForeignKey("recipes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title_snapshot", sa.String(255), nullable=True),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column(
            "assignee_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_by_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("meal_plan_day_id", "meal_schedule_id", name="uq_plan_item_schedule"),
    )
    op.create_index("ix_meal_plan_items_day", "meal_plan_items", ["meal_plan_day_id"])
    op.create_index("ix_meal_plan_items_schedule", "meal_plan_items", ["meal_schedule_id"])
    op.create_index("ix_meal_plan_items_recipe", "meal_plan_items", ["recipe_id"])
    op.create_index("ix_meal_plan_items_assignee", "meal_plan_items", ["assignee_user_id"])

    op.create_table(
        "family_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "pregnancy_episode_id",
            sa.String(36),
            sa.ForeignKey("pregnancy_episodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subject_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("task_date", sa.Date(), nullable=False),
        sa.Column("task_type", sa.String(24), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column(
            "assignee_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "created_by_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "completed_by_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_family_tasks_episode", "family_tasks", ["pregnancy_episode_id"])
    op.create_index("ix_family_tasks_subject", "family_tasks", ["subject_user_id"])
    op.create_index("ix_family_tasks_date", "family_tasks", ["task_date"])
    op.create_index("ix_family_tasks_assignee", "family_tasks", ["assignee_user_id"])
    op.create_index("ix_family_tasks_status", "family_tasks", ["status"])
    op.create_index("ix_family_tasks_creator", "family_tasks", ["created_by_user_id"])


def downgrade() -> None:
    op.drop_table("family_tasks")
    op.drop_table("meal_plan_items")
    op.drop_table("meal_plan_days")
