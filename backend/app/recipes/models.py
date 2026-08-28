from decimal import Decimal
from uuid import uuid4

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    minutes: Mapped[int] = mapped_column(Integer, default=15)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_status: Mapped[str] = mapped_column(String(20), default="published", index=True)
    content_version: Mapped[str] = mapped_column(String(40), default="v1")
    pregnancy_safety: Mapped[str] = mapped_column(String(20), default="safe", index=True)
    safety_summary: Mapped[str] = mapped_column(String(255), default="食材信息已复核")
    allergen_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    subtitle: Mapped[str | None] = mapped_column(String(120), nullable=True)
    energy_kcal: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    protein_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    fat_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    carbohydrate_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    fiber_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    source_type: Mapped[str] = mapped_column(String(20), default="platform", index=True)
    owner_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    visibility: Mapped[str] = mapped_column(String(20), default="platform", index=True)
    original_query: Mapped[str | None] = mapped_column(String(300), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    safety_rule_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nutrition_source: Mapped[str] = mapped_column(String(20), default="tka", index=True)
    nutrition_confidence: Mapped[str] = mapped_column(String(20), default="high", index=True)
    content_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    items: Mapped[list["RecipeItem"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", order_by="RecipeItem.position"
    )
    favorites: Mapped[list["RecipeFavorite"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )


class RecipeItem(Base):
    __tablename__ = "recipe_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    source_food_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ingredient_name_zh: Mapped[str] = mapped_column(String(120), default="")
    original_measure: Mapped[str] = mapped_column(String(80), default="")
    grams: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    position: Mapped[int] = mapped_column(Integer, default=0)
    nutrition_source: Mapped[str] = mapped_column(String(20), default="tka")
    estimated_energy_kcal_per_100g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    estimated_protein_g_per_100g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    estimated_fat_g_per_100g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    estimated_carbohydrate_g_per_100g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    estimated_fiber_g_per_100g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    recipe: Mapped[Recipe] = relationship(back_populates="items")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RecipeFavorite(Base):
    __tablename__ = "recipe_favorites"
    __table_args__ = (UniqueConstraint("user_id", "recipe_id", name="uq_recipe_favorite_user_recipe"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    recipe: Mapped[Recipe] = relationship(back_populates="favorites")
