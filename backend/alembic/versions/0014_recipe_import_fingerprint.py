"""separate import revision from canonical recipe fingerprint

Revision ID: 0014_recipe_import_fingerprint
Revises: 0013_recipe_steps
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0014_recipe_import_fingerprint"
down_revision: str | None = "0013_recipe_steps"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("recipes") as batch:
        batch.add_column(sa.Column("import_fingerprint", sa.String(length=64), nullable=True))
        batch.create_index("ix_recipes_import_fingerprint", ["import_fingerprint"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("recipes") as batch:
        batch.drop_index("ix_recipes_import_fingerprint")
        batch.drop_column("import_fingerprint")
