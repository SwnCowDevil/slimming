"""create consent-based family collaboration tables

Revision ID: 0008_family_collaboration
Revises: 0007_tracking_ownership
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0008_family_collaboration"
down_revision: str | None = "0007_tracking_ownership"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "family_invitations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "pregnancy_episode_id",
            sa.String(36),
            sa.ForeignKey("pregnancy_episodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "invited_by_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "accepted_by_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_family_invitations_episode", "family_invitations", ["pregnancy_episode_id"])
    op.create_index("ix_family_invitations_inviter", "family_invitations", ["invited_by_user_id"])
    op.create_index("ix_family_invitations_token_hash", "family_invitations", ["token_hash"], unique=True)
    op.create_index("ix_family_invitations_expires_at", "family_invitations", ["expires_at"])

    op.create_table(
        "family_memberships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "pregnancy_episode_id",
            sa.String(36),
            sa.ForeignKey("pregnancy_episodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "owner_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "member_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(24), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("permission_scopes", sa.JSON(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "pregnancy_episode_id", "member_user_id", name="uq_family_episode_member"
        ),
    )
    op.create_index("ix_family_memberships_episode", "family_memberships", ["pregnancy_episode_id"])
    op.create_index("ix_family_memberships_owner", "family_memberships", ["owner_user_id"])
    op.create_index("ix_family_memberships_member", "family_memberships", ["member_user_id"])
    op.create_index("ix_family_memberships_status", "family_memberships", ["status"])

    op.create_table(
        "consent_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "pregnancy_episode_id",
            sa.String(36),
            sa.ForeignKey("pregnancy_episodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "actor_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "membership_id",
            sa.String(36),
            sa.ForeignKey("family_memberships.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("event_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_consent_events_episode", "consent_events", ["pregnancy_episode_id"])
    op.create_index("ix_consent_events_actor", "consent_events", ["actor_user_id"])
    op.create_index("ix_consent_events_membership", "consent_events", ["membership_id"])
    op.create_index("ix_consent_events_type", "consent_events", ["event_type"])


def downgrade() -> None:
    op.drop_table("consent_events")
    op.drop_table("family_memberships")
    op.drop_table("family_invitations")
