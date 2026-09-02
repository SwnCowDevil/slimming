"""add ownership and pregnancy context to tracking records

Revision ID: 0007_tracking_ownership
Revises: 0006_pregnancy_core
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0007_tracking_ownership"
down_revision: str | None = "0006_pregnancy_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("meal_entries") as batch:
        batch.add_column(sa.Column("pregnancy_episode_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("subject_user_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("created_by_user_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("meal_schedule_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("meal_name_snapshot", sa.String(40), nullable=True))
        batch.add_column(
            sa.Column(
                "recorded_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            )
        )
        batch.add_column(sa.Column("note", sa.Text(), nullable=True))
        batch.create_foreign_key(
            "fk_meal_entries_pregnancy_episode",
            "pregnancy_episodes",
            ["pregnancy_episode_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_foreign_key(
            "fk_meal_entries_subject_user",
            "users",
            ["subject_user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch.create_foreign_key(
            "fk_meal_entries_created_by_user",
            "users",
            ["created_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_foreign_key(
            "fk_meal_entries_meal_schedule",
            "meal_schedules",
            ["meal_schedule_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        sa.text(
            "UPDATE meal_entries "
            "SET subject_user_id = user_id, created_by_user_id = user_id, "
            "meal_name_snapshot = CASE meal_type "
            "WHEN 'breakfast' THEN '早餐' WHEN 'lunch' THEN '午餐' "
            "WHEN 'dinner' THEN '晚餐' ELSE '加餐' END"
        )
    )
    op.create_index("ix_meal_entries_pregnancy_episode_id", "meal_entries", ["pregnancy_episode_id"])
    op.create_index("ix_meal_entries_subject_user_id", "meal_entries", ["subject_user_id"])
    op.create_index("ix_meal_entries_created_by_user_id", "meal_entries", ["created_by_user_id"])
    op.create_index("ix_meal_entries_meal_schedule_id", "meal_entries", ["meal_schedule_id"])

    with op.batch_alter_table("weight_entries") as batch:
        batch.add_column(sa.Column("pregnancy_episode_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("subject_user_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("created_by_user_id", sa.String(36), nullable=True))
        batch.create_foreign_key(
            "fk_weight_entries_pregnancy_episode",
            "pregnancy_episodes",
            ["pregnancy_episode_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_foreign_key(
            "fk_weight_entries_subject_user",
            "users",
            ["subject_user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch.create_foreign_key(
            "fk_weight_entries_created_by_user",
            "users",
            ["created_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        sa.text(
            "UPDATE weight_entries "
            "SET subject_user_id = user_id, created_by_user_id = user_id"
        )
    )
    op.create_index("ix_weight_entries_pregnancy_episode_id", "weight_entries", ["pregnancy_episode_id"])
    op.create_index("ix_weight_entries_subject_user_id", "weight_entries", ["subject_user_id"])
    op.create_index("ix_weight_entries_created_by_user_id", "weight_entries", ["created_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_weight_entries_created_by_user_id", table_name="weight_entries")
    op.drop_index("ix_weight_entries_subject_user_id", table_name="weight_entries")
    op.drop_index("ix_weight_entries_pregnancy_episode_id", table_name="weight_entries")
    with op.batch_alter_table("weight_entries") as batch:
        batch.drop_column("created_by_user_id")
        batch.drop_column("subject_user_id")
        batch.drop_column("pregnancy_episode_id")

    op.drop_index("ix_meal_entries_meal_schedule_id", table_name="meal_entries")
    op.drop_index("ix_meal_entries_created_by_user_id", table_name="meal_entries")
    op.drop_index("ix_meal_entries_subject_user_id", table_name="meal_entries")
    op.drop_index("ix_meal_entries_pregnancy_episode_id", table_name="meal_entries")
    with op.batch_alter_table("meal_entries") as batch:
        batch.drop_column("note")
        batch.drop_column("recorded_at")
        batch.drop_column("meal_name_snapshot")
        batch.drop_column("meal_schedule_id")
        batch.drop_column("created_by_user_id")
        batch.drop_column("subject_user_id")
        batch.drop_column("pregnancy_episode_id")
