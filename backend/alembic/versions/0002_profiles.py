"""create body profiles

Revision ID: 0002_profiles
Revises: 0001_initial
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_profiles"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "body_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("goal", sa.String(20), nullable=False),
        sa.Column("sex", sa.String(10), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("height_cm", sa.Numeric(6, 2), nullable=False),
        sa.Column("current_weight_kg", sa.Numeric(6, 2), nullable=False),
        sa.Column("target_weight_kg", sa.Numeric(6, 2), nullable=False),
        sa.Column("activity_level", sa.String(20), nullable=False),
        sa.Column("dietary_preferences", sa.JSON(), nullable=False),
        sa.Column("allergens", sa.JSON(), nullable=False),
        sa.Column("eating_out_frequency", sa.String(20), nullable=False),
        sa.Column("bmi", sa.Numeric(5, 1), nullable=False),
        sa.Column("bmr", sa.Numeric(7, 0), nullable=False),
        sa.Column("minimum_kcal", sa.Integer(), nullable=False),
        sa.Column("maximum_kcal", sa.Integer(), nullable=False),
        sa.Column("daily_kcal", sa.Integer(), nullable=False),
        sa.Column("protein_g", sa.Integer(), nullable=False),
        sa.Column("carbohydrate_g", sa.Integer(), nullable=False),
        sa.Column("fat_g", sa.Integer(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_body_profiles_user_id"),
    )
    op.create_index("ix_body_profiles_user_id", "body_profiles", ["user_id"])


def downgrade() -> None:
    op.drop_table("body_profiles")
