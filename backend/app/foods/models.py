from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Date, DateTime, ForeignKey, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Food(Base):
    __tablename__ = "foods"
    __table_args__ = (UniqueConstraint("provider", "source_food_id", name="uq_food_provider_source"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    provider: Mapped[str] = mapped_column(String(32), index=True)
    source_food_id: Mapped[str] = mapped_column(String(128), index=True)
    source_url: Mapped[str] = mapped_column(String(500))
    foodex2_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name_en: Mapped[str] = mapped_column(String(255), index=True)
    name_et: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    synonyms: Mapped[list[str]] = mapped_column(JSON, default=list)
    food_group: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_updated_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    household_measures: Mapped[list[dict]] = mapped_column(JSON, default=list)
    energy_kcal_100g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    protein_g_100g: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=0)
    fat_g_100g: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=0)
    carbohydrate_g_100g: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=0)
    fiber_g_100g: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=0)
    salt_g_100g: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=0)
    method_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    source_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    dataset_version: Mapped[str] = mapped_column(String(128), index=True)
    raw_sha256: Mapped[str] = mapped_column(String(64))
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    aliases: Mapped[list["FoodAlias"]] = relationship(back_populates="food", cascade="all, delete-orphan")


class FoodAlias(Base):
    __tablename__ = "food_aliases"
    __table_args__ = (UniqueConstraint("food_id", "locale", "name", name="uq_food_alias"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    food_id: Mapped[str] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"), index=True)
    locale: Mapped[str] = mapped_column(String(16), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)

    food: Mapped[Food] = relationship(back_populates="aliases")

