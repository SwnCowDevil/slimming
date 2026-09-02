"""create users and WeChat identities

Revision ID: 0001_initial
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("nickname", sa.String(80), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "wechat_identities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("app_id", sa.String(64), nullable=False),
        sa.Column("openid", sa.String(128), nullable=False),
        sa.Column("unionid", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("app_id", "openid", name="uq_wechat_app_openid"),
    )
    op.create_index("ix_wechat_identities_user_id", "wechat_identities", ["user_id"])
    op.create_index("ix_wechat_identities_unionid", "wechat_identities", ["unionid"])


def downgrade() -> None:
    op.drop_table("wechat_identities")
    op.drop_table("users")
