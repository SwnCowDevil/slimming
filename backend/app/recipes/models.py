from decimal import Decimal
from uuid import uuid4

from sqlalchemy import ForeignKey, Integer, JSON, Numeric, String, Text
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
    items: Mapped[list["RecipeItem"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", order_by="RecipeItem.position"
    )


class RecipeItem(Base):
    __tablename__ = "recipe_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    source_food_id: Mapped[str] = mapped_column(String(128))
    grams: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    position: Mapped[int] = mapped_column(Integer, default=0)
    recipe: Mapped[Recipe] = relationship(back_populates="items")
