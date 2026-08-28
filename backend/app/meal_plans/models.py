from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MealPlanDay(Base):
    __tablename__ = "meal_plan_days"
    __table_args__ = (
        UniqueConstraint("pregnancy_episode_id", "plan_date", name="uq_meal_plan_episode_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    pregnancy_episode_id: Mapped[str] = mapped_column(
        ForeignKey("pregnancy_episodes.id", ondelete="CASCADE"), index=True
    )
    subject_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    plan_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    rule_version: Mapped[str] = mapped_column(String(32), default="schedule-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    items: Mapped[list["MealPlanItem"]] = relationship(
        back_populates="plan_day",
        cascade="all, delete-orphan",
        order_by="MealPlanItem.position",
    )


class MealPlanItem(Base):
    __tablename__ = "meal_plan_items"
    __table_args__ = (
        UniqueConstraint("meal_plan_day_id", "meal_schedule_id", name="uq_plan_item_schedule"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    meal_plan_day_id: Mapped[str] = mapped_column(
        ForeignKey("meal_plan_days.id", ondelete="CASCADE"), index=True
    )
    meal_schedule_id: Mapped[str] = mapped_column(
        ForeignKey("meal_schedules.id", ondelete="RESTRICT"), index=True
    )
    meal_name_snapshot: Mapped[str] = mapped_column(String(40))
    scheduled_time_snapshot: Mapped[str] = mapped_column(String(5))
    position: Mapped[int] = mapped_column(Integer)
    recipe_id: Mapped[str | None] = mapped_column(
        ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title_snapshot: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str] = mapped_column(String(24), default="pending")
    assignee_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    updated_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    plan_day: Mapped[MealPlanDay] = relationship(back_populates="items")
