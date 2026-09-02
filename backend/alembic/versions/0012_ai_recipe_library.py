"""add private AI recipe library and recommendation sessions

Revision ID: 0012_ai_recipe_library
Revises: 0011_ai_policy
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0012_ai_recipe_library"
down_revision: str | None = "0011_ai_policy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("recipes") as batch:
        batch.add_column(sa.Column("source_type", sa.String(20), nullable=False, server_default="platform"))
        batch.add_column(sa.Column("owner_user_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("visibility", sa.String(20), nullable=False, server_default="platform"))
        batch.add_column(sa.Column("original_query", sa.String(300), nullable=True))
        batch.add_column(sa.Column("model_name", sa.String(128), nullable=True))
        batch.add_column(sa.Column("prompt_version", sa.String(64), nullable=True))
        batch.add_column(sa.Column("safety_rule_version", sa.String(64), nullable=True))
        batch.add_column(sa.Column("nutrition_source", sa.String(20), nullable=False, server_default="tka"))
        batch.add_column(sa.Column("nutrition_confidence", sa.String(20), nullable=False, server_default="high"))
        batch.add_column(sa.Column("content_fingerprint", sa.String(64), nullable=True))
        batch.create_foreign_key(
            "fk_recipes_owner_user",
            "users",
            ["owner_user_id"],
            ["id"],
            ondelete="CASCADE",
        )
    op.create_index("ix_recipes_source_type", "recipes", ["source_type"])
    op.create_index("ix_recipes_owner_user_id", "recipes", ["owner_user_id"])
    op.create_index("ix_recipes_visibility", "recipes", ["visibility"])
    op.create_index("ix_recipes_nutrition_source", "recipes", ["nutrition_source"])
    op.create_index("ix_recipes_nutrition_confidence", "recipes", ["nutrition_confidence"])
    op.create_index("ix_recipes_content_fingerprint", "recipes", ["content_fingerprint"])

    with op.batch_alter_table("recipe_items") as batch:
        batch.alter_column("source_food_id", existing_type=sa.String(128), nullable=True)
        batch.add_column(sa.Column("ingredient_name_zh", sa.String(120), nullable=False, server_default=""))
        batch.add_column(sa.Column("original_measure", sa.String(80), nullable=False, server_default=""))
        batch.add_column(sa.Column("nutrition_source", sa.String(20), nullable=False, server_default="tka"))
        batch.add_column(sa.Column("estimated_energy_kcal_per_100g", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("estimated_protein_g_per_100g", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("estimated_fat_g_per_100g", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("estimated_carbohydrate_g_per_100g", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("estimated_fiber_g_per_100g", sa.Numeric(10, 2), nullable=True))

    op.create_table(
        "recipe_favorites",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipe_id", sa.String(64), sa.ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "recipe_id", name="uq_recipe_favorite_user_recipe"),
    )
    op.create_index("ix_recipe_favorites_user_id", "recipe_favorites", ["user_id"])
    op.create_index("ix_recipe_favorites_recipe_id", "recipe_favorites", ["recipe_id"])

    op.create_table(
        "ai_recommendation_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("displayed_fingerprints", sa.JSON(), nullable=False),
        sa.Column("candidates", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_recommendation_sessions_user_id", "ai_recommendation_sessions", ["user_id"])
    op.create_index("ix_ai_recommendation_sessions_expires_at", "ai_recommendation_sessions", ["expires_at"])

    op.create_table(
        "ai_recipe_request_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("ai_recommendation_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("request_kind", sa.String(16), nullable=False),
        sa.Column("request_ip_hash", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=False),
        sa.Column("provider_call_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_model", sa.String(128), nullable=True),
        sa.Column("prompt_version", sa.String(64), nullable=True),
        sa.Column("provider_latency_ms", sa.Integer(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("rejected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fallback_reason", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_ai_recipe_event_user_idempotency"),
    )
    op.create_index("ix_ai_recipe_request_events_session_id", "ai_recipe_request_events", ["session_id"])
    op.create_index("ix_ai_recipe_request_events_user_id", "ai_recipe_request_events", ["user_id"])
    op.create_index("ix_ai_recipe_request_events_request_ip_hash", "ai_recipe_request_events", ["request_ip_hash"])
    op.create_index("ix_ai_recipe_request_events_created_at", "ai_recipe_request_events", ["created_at"])

    with op.batch_alter_table("meal_entries") as batch:
        batch.alter_column("food_id", existing_type=sa.String(36), nullable=True)
        batch.add_column(sa.Column("source_recipe_id", sa.String(64), nullable=True))
        batch.add_column(sa.Column("nutrition_source", sa.String(20), nullable=False, server_default="tka"))
        batch.create_foreign_key(
            "fk_meal_entries_source_recipe",
            "recipes",
            ["source_recipe_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index("ix_meal_entries_source_recipe_id", "meal_entries", ["source_recipe_id"])


def downgrade() -> None:
    op.drop_index("ix_meal_entries_source_recipe_id", table_name="meal_entries")
    with op.batch_alter_table("meal_entries") as batch:
        batch.drop_constraint("fk_meal_entries_source_recipe", type_="foreignkey")
        batch.drop_column("nutrition_source")
        batch.drop_column("source_recipe_id")
        batch.alter_column("food_id", existing_type=sa.String(36), nullable=False)

    op.drop_index("ix_ai_recipe_request_events_created_at", table_name="ai_recipe_request_events")
    op.drop_index("ix_ai_recipe_request_events_request_ip_hash", table_name="ai_recipe_request_events")
    op.drop_index("ix_ai_recipe_request_events_user_id", table_name="ai_recipe_request_events")
    op.drop_index("ix_ai_recipe_request_events_session_id", table_name="ai_recipe_request_events")
    op.drop_table("ai_recipe_request_events")
    op.drop_index("ix_ai_recommendation_sessions_expires_at", table_name="ai_recommendation_sessions")
    op.drop_index("ix_ai_recommendation_sessions_user_id", table_name="ai_recommendation_sessions")
    op.drop_table("ai_recommendation_sessions")
    op.drop_index("ix_recipe_favorites_recipe_id", table_name="recipe_favorites")
    op.drop_index("ix_recipe_favorites_user_id", table_name="recipe_favorites")
    op.drop_table("recipe_favorites")

    with op.batch_alter_table("recipe_items") as batch:
        batch.drop_column("estimated_fiber_g_per_100g")
        batch.drop_column("estimated_carbohydrate_g_per_100g")
        batch.drop_column("estimated_fat_g_per_100g")
        batch.drop_column("estimated_protein_g_per_100g")
        batch.drop_column("estimated_energy_kcal_per_100g")
        batch.drop_column("nutrition_source")
        batch.drop_column("original_measure")
        batch.drop_column("ingredient_name_zh")
        batch.alter_column("source_food_id", existing_type=sa.String(128), nullable=False)

    op.drop_index("ix_recipes_content_fingerprint", table_name="recipes")
    op.drop_index("ix_recipes_nutrition_confidence", table_name="recipes")
    op.drop_index("ix_recipes_nutrition_source", table_name="recipes")
    op.drop_index("ix_recipes_visibility", table_name="recipes")
    op.drop_index("ix_recipes_owner_user_id", table_name="recipes")
    op.drop_index("ix_recipes_source_type", table_name="recipes")
    with op.batch_alter_table("recipes") as batch:
        batch.drop_constraint("fk_recipes_owner_user", type_="foreignkey")
        batch.drop_column("content_fingerprint")
        batch.drop_column("nutrition_confidence")
        batch.drop_column("nutrition_source")
        batch.drop_column("safety_rule_version")
        batch.drop_column("prompt_version")
        batch.drop_column("model_name")
        batch.drop_column("original_query")
        batch.drop_column("visibility")
        batch.drop_column("owner_user_id")
        batch.drop_column("source_type")
