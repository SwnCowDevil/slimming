from decimal import Decimal
from uuid import uuid4

from sqlalchemy import ForeignKey, Integer, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BodyProfile(Base):
    __tablename__ = "body_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_body_profiles_user_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    goal: Mapped[str] = mapped_column(String(20))
    sex: Mapped[str] = mapped_column(String(10))
    age: Mapped[int] = mapped_column(Integer)
    height_cm: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    current_weight_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    target_weight_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    activity_level: Mapped[str] = mapped_column(String(20))
    dietary_preferences: Mapped[list[str]] = mapped_column(JSON, default=list)
    allergens: Mapped[list[str]] = mapped_column(JSON, default=list)
    eating_out_frequency: Mapped[str] = mapped_column(String(20))
    bmi: Mapped[Decimal] = mapped_column(Numeric(5, 1))
    bmr: Mapped[Decimal] = mapped_column(Numeric(7, 0))
    minimum_kcal: Mapped[int] = mapped_column(Integer)
    maximum_kcal: Mapped[int] = mapped_column(Integer)
    daily_kcal: Mapped[int] = mapped_column(Integer)
    protein_g: Mapped[int] = mapped_column(Integer)
    carbohydrate_g: Mapped[int] = mapped_column(Integer)
    fat_g: Mapped[int] = mapped_column(Integer)

