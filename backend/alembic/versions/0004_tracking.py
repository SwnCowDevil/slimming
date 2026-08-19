"""create tracking tables

Revision ID: 0004_tracking
Revises: 0003_food_catalog
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "0004_tracking"
down_revision: str | None = "0003_food_catalog"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table("meal_entries",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("meal_date", sa.Date(), nullable=False), sa.Column("meal_type", sa.String(20), nullable=False), sa.Column("food_id", sa.String(36), sa.ForeignKey("foods.id"), nullable=False),
        sa.Column("source_food_id", sa.String(128), nullable=False), sa.Column("food_name", sa.String(255), nullable=False), sa.Column("grams", sa.Numeric(10,2), nullable=False),
        sa.Column("energy_kcal", sa.Numeric(10,2), nullable=False), sa.Column("protein_g", sa.Numeric(10,2), nullable=False), sa.Column("fat_g", sa.Numeric(10,2), nullable=False),
        sa.Column("carbohydrate_g", sa.Numeric(10,2), nullable=False), sa.Column("fiber_g", sa.Numeric(10,2), nullable=False), sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("dataset_version", sa.String(128), nullable=False), sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_meal_user_idempotency"))
    op.create_index("ix_meal_entries_user_id", "meal_entries", ["user_id"]); op.create_index("ix_meal_entries_meal_date", "meal_entries", ["meal_date"])
    op.create_table("weight_entries", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("recorded_date", sa.Date(), nullable=False), sa.Column("weight_kg", sa.Numeric(6,2), nullable=False), sa.UniqueConstraint("user_id", "recorded_date", name="uq_weight_user_date"))
    op.create_index("ix_weight_entries_user_id", "weight_entries", ["user_id"]); op.create_index("ix_weight_entries_recorded_date", "weight_entries", ["recorded_date"])
    op.create_table("daily_habits", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("habit_date", sa.Date(), nullable=False), sa.Column("water_ml", sa.Integer(), nullable=False), sa.Column("steps", sa.Integer(), nullable=False), sa.UniqueConstraint("user_id", "habit_date", name="uq_habit_user_date"))
    op.create_index("ix_daily_habits_user_id", "daily_habits", ["user_id"]); op.create_index("ix_daily_habits_habit_date", "daily_habits", ["habit_date"])


def downgrade() -> None:
    op.drop_table("daily_habits"); op.drop_table("weight_entries"); op.drop_table("meal_entries")
