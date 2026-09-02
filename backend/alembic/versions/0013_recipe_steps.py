"""persist recipe cooking steps

Revision ID: 0013_recipe_steps
Revises: 0012_ai_recipe_library
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0013_recipe_steps"
down_revision: str | None = "0012_ai_recipe_library"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("recipes") as batch:
        batch.add_column(sa.Column("steps", sa.JSON(), nullable=False, server_default="[]"))


def downgrade() -> None:
    with op.batch_alter_table("recipes") as batch:
        batch.drop_column("steps")
