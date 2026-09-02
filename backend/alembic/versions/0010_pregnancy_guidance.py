"""add reviewed pregnancy recipe metadata

Revision ID: 0010_pregnancy_guidance
Revises: 0009_meal_plans
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0010_pregnancy_guidance"
down_revision: str | None = "0009_meal_plans"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("recipes") as batch:
        batch.add_column(
            sa.Column("content_status", sa.String(20), nullable=False, server_default="published")
        )
        batch.add_column(
            sa.Column("content_version", sa.String(40), nullable=False, server_default="v1")
        )
        batch.add_column(
            sa.Column("pregnancy_safety", sa.String(20), nullable=False, server_default="safe")
        )
        batch.add_column(
            sa.Column(
                "safety_summary",
                sa.String(255),
                nullable=False,
                server_default="食材信息已复核",
            )
        )
        batch.add_column(sa.Column("allergen_codes", sa.JSON(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("subtitle", sa.String(120), nullable=True))
        batch.add_column(sa.Column("energy_kcal", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("protein_g", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("fat_g", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("carbohydrate_g", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("fiber_g", sa.Numeric(10, 2), nullable=True))
    op.create_index("ix_recipes_content_status", "recipes", ["content_status"])
    op.create_index("ix_recipes_pregnancy_safety", "recipes", ["pregnancy_safety"])


def downgrade() -> None:
    op.drop_index("ix_recipes_pregnancy_safety", table_name="recipes")
    op.drop_index("ix_recipes_content_status", table_name="recipes")
    with op.batch_alter_table("recipes") as batch:
        batch.drop_column("fiber_g")
        batch.drop_column("carbohydrate_g")
        batch.drop_column("fat_g")
        batch.drop_column("protein_g")
        batch.drop_column("energy_kcal")
        batch.drop_column("subtitle")
        batch.drop_column("allergen_codes")
        batch.drop_column("safety_summary")
        batch.drop_column("pregnancy_safety")
        batch.drop_column("content_version")
        batch.drop_column("content_status")
