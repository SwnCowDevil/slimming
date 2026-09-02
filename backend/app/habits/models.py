from datetime import date
from uuid import uuid4

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DailyHabit(Base):
    __tablename__ = "daily_habits"
    __table_args__ = (UniqueConstraint("user_id", "habit_date", name="uq_habit_user_date"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    habit_date: Mapped[date] = mapped_column(Date, index=True)
    water_ml: Mapped[int] = mapped_column(Integer, default=0)
    steps: Mapped[int] = mapped_column(Integer, default=0)

