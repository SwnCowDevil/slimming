from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PregnancyEpisode(Base):
    __tablename__ = "pregnancy_episodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    due_date: Mapped[date] = mapped_column(Date, index=True)
    due_date_source: Mapped[str] = mapped_column(String(32), default="user_entered")
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Shanghai")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    preferences: Mapped["PregnancyPreference"] = relationship(
        back_populates="episode", cascade="all, delete-orphan", uselist=False
    )
    meal_schedules: Mapped[list["MealSchedule"]] = relationship(
        back_populates="episode", cascade="all, delete-orphan"
    )


class PregnancyPreference(Base):
    __tablename__ = "pregnancy_preferences"
    __table_args__ = (
        UniqueConstraint("pregnancy_episode_id", name="uq_pregnancy_preferences_episode"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    pregnancy_episode_id: Mapped[str] = mapped_column(
        ForeignKey("pregnancy_episodes.id", ondelete="CASCADE"), index=True
    )
    height_cm: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    pre_pregnancy_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    activity_level: Mapped[str] = mapped_column(String(20))
    dietary_preferences: Mapped[list[str]] = mapped_column(JSON, default=list)
    allergens: Mapped[list[str]] = mapped_column(JSON, default=list)
    avoidances: Mapped[list[str]] = mapped_column(JSON, default=list)
    disliked_foods: Mapped[list[str]] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    episode: Mapped[PregnancyEpisode] = relationship(back_populates="preferences")


class MealSchedule(Base):
    __tablename__ = "meal_schedules"
    __table_args__ = (
        UniqueConstraint("pregnancy_episode_id", "code", name="uq_meal_schedule_episode_code"),
        UniqueConstraint("pregnancy_episode_id", "position", name="uq_meal_schedule_episode_position"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    pregnancy_episode_id: Mapped[str] = mapped_column(
        ForeignKey("pregnancy_episodes.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(32))
    display_name: Mapped[str] = mapped_column(String(40))
    scheduled_time: Mapped[str] = mapped_column(String(5))
    position: Mapped[int] = mapped_column(Integer)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    episode: Mapped[PregnancyEpisode] = relationship(back_populates="meal_schedules")


class DailyWellbeingLog(Base):
    __tablename__ = "daily_wellbeing_logs"
    __table_args__ = (
        UniqueConstraint("pregnancy_episode_id", "log_date", name="uq_wellbeing_episode_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    pregnancy_episode_id: Mapped[str] = mapped_column(
        ForeignKey("pregnancy_episodes.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    log_date: Mapped[date] = mapped_column(Date, index=True)
    feeling_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
