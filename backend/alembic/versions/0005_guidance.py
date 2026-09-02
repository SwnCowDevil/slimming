"""create recipes, guidance and matching tables

Revision ID: 0005_guidance
Revises: 0004_tracking
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0005_guidance"
down_revision: str | None = "0004_tracking"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recipes",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("image_url", sa.String(500), nullable=True),
    )
    op.create_index("ix_recipes_title", "recipes", ["title"])
    op.create_table(
        "recipe_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("recipe_id", sa.String(64), sa.ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_food_id", sa.String(128), nullable=False),
        sa.Column("grams", sa.Numeric(10, 2), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
    )
    op.create_index("ix_recipe_items_recipe_id", "recipe_items", ["recipe_id"])
    op.create_table(
        "ai_drafts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("candidate", sa.JSON(), nullable=False),
        sa.Column("input_data_range", sa.JSON(), nullable=False),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.String(64), nullable=False),
        sa.Column("safety_action", sa.String(32), nullable=False),
        sa.Column("meal_entry_id", sa.String(36), sa.ForeignKey("meal_entries.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_drafts_user_id", "ai_drafts", ["user_id"])
    op.create_table(
        "dietitians",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("specialties", sa.JSON(), nullable=False),
        sa.Column("credentials", sa.String(255), nullable=False),
        sa.Column("bio", sa.Text(), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
    )
    op.create_table(
        "dietitian_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dietitian_id", sa.String(64), sa.ForeignKey("dietitians.id"), nullable=False),
        sa.Column("goal", sa.String(120), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_dietitian_requests_user_id", "dietitian_requests", ["user_id"])
    op.create_index("ix_dietitian_requests_dietitian_id", "dietitian_requests", ["dietitian_id"])
    op.create_table(
        "media_uploads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False, unique=True),
        sa.Column("content_type", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_media_uploads_user_id", "media_uploads", ["user_id"])


def downgrade() -> None:
    op.drop_table("media_uploads")
    op.drop_table("dietitian_requests")
    op.drop_table("dietitians")
    op.drop_table("ai_drafts")
    op.drop_table("recipe_items")
    op.drop_table("recipes")
