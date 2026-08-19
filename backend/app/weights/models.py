from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WeightEntry(Base):
    __tablename__ = "weight_entries"
    __table_args__ = (UniqueConstraint("user_id", "recorded_date", name="uq_weight_user_date"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    recorded_date: Mapped[date] = mapped_column(Date, index=True)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2))

