from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MealEntry(Base):
    __tablename__ = "meal_entries"
    __table_args__ = (UniqueConstraint("user_id", "idempotency_key", name="uq_meal_user_idempotency"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    pregnancy_episode_id: Mapped[str | None] = mapped_column(
        ForeignKey("pregnancy_episodes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subject_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    created_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    meal_schedule_id: Mapped[str | None] = mapped_column(
        ForeignKey("meal_schedules.id", ondelete="SET NULL"), nullable=True, index=True
    )
    meal_name_snapshot: Mapped[str | None] = mapped_column(String(40), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
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
