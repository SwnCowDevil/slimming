"""create food catalog

Revision ID: 0003_food_catalog
Revises: 0002_profiles
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_food_catalog"
down_revision: str | None = "0002_profiles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "foods",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("source_food_id", sa.String(128), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=False),
        sa.Column("foodex2_code", sa.String(255)),
        sa.Column("name_en", sa.String(255), nullable=False),
        sa.Column("name_et", sa.String(255)),
        sa.Column("synonyms", sa.JSON(), nullable=False),
        sa.Column("food_group", sa.String(255)),
        sa.Column("source_updated_at", sa.Date()),
        sa.Column("household_measures", sa.JSON(), nullable=False),
        sa.Column("energy_kcal_100g", sa.Numeric(10, 2), nullable=False),
        sa.Column("protein_g_100g", sa.Numeric(10, 3), nullable=False),
        sa.Column("fat_g_100g", sa.Numeric(10, 3), nullable=False),
        sa.Column("carbohydrate_g_100g", sa.Numeric(10, 3), nullable=False),
        sa.Column("fiber_g_100g", sa.Numeric(10, 3), nullable=False),
        sa.Column("salt_g_100g", sa.Numeric(10, 3), nullable=False),
        sa.Column("method_ids", sa.JSON(), nullable=False),
        sa.Column("source_ids", sa.JSON(), nullable=False),
        sa.Column("dataset_version", sa.String(128), nullable=False),
        sa.Column("raw_sha256", sa.String(64), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider", "source_food_id", name="uq_food_provider_source"),
    )
    op.create_index("ix_foods_provider", "foods", ["provider"])
    op.create_index("ix_foods_source_food_id", "foods", ["source_food_id"])
    op.create_index("ix_foods_name_en", "foods", ["name_en"])
    op.create_index("ix_foods_name_et", "foods", ["name_et"])
    op.create_index("ix_foods_dataset_version", "foods", ["dataset_version"])
    op.create_table(
        "food_aliases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("food_id", sa.String(36), sa.ForeignKey("foods.id", ondelete="CASCADE"), nullable=False),
        sa.Column("locale", sa.String(16), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.UniqueConstraint("food_id", "locale", "name", name="uq_food_alias"),
    )
    op.create_index("ix_food_aliases_food_id", "food_aliases", ["food_id"])
    op.create_index("ix_food_aliases_locale", "food_aliases", ["locale"])
    op.create_index("ix_food_aliases_name", "food_aliases", ["name"])


def downgrade() -> None:
    op.drop_table("food_aliases")
    op.drop_table("foods")
