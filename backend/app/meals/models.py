from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MealEntry(Base):
    __tablename__ = "meal_entries"
    __table_args__ = (UniqueConstraint("user_id", "idempotency_key", name="uq_meal_user_idempotency"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    meal_date: Mapped[date] = mapped_column(Date, index=True)
    meal_type: Mapped[str] = mapped_column(String(20))
    food_id: Mapped[str] = mapped_column(ForeignKey("foods.id"), index=True)
    source_food_id: Mapped[str] = mapped_column(String(128))
    food_name: Mapped[str] = mapped_column(String(255))
    grams: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    energy_kcal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    protein_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    fat_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    carbohydrate_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    fiber_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    provider: Mapped[str] = mapped_column(String(32))
    dataset_version: Mapped[str] = mapped_column(String(128))
    idempotency_key: Mapped[str] = mapped_column(String(128))

