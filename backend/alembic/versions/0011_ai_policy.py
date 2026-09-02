"""add pregnancy AI policy metadata

Revision ID: 0011_ai_policy
Revises: 0010_pregnancy_guidance
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0011_ai_policy"
down_revision: str | None = "0010_pregnancy_guidance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("ai_drafts") as batch:
        batch.add_column(
            sa.Column(
                "policy_version",
                sa.String(64),
                nullable=False,
                server_default="legacy-safety-v1",
            )
        )
        batch.add_column(sa.Column("response_text", sa.String(1000), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("ai_drafts") as batch:
        batch.drop_column("response_text")
        batch.drop_column("policy_version")
