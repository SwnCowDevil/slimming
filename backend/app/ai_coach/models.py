from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AiDraft(Base):
    __tablename__ = "ai_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    candidate: Mapped[dict] = mapped_column(JSON)
    input_data_range: Mapped[dict] = mapped_column(JSON, default=dict)
    model_name: Mapped[str] = mapped_column(String(128), default="rules-v1")
    prompt_version: Mapped[str] = mapped_column(String(64), default="meal-candidate-v1")
    safety_action: Mapped[str] = mapped_column(String(32), default="allow")
    policy_version: Mapped[str] = mapped_column(String(64), default="legacy-safety-v1")
    response_text: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    meal_entry_id: Mapped[str | None] = mapped_column(ForeignKey("meal_entries.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class AiCoachRateLimitReservation(Base):
    __tablename__ = "ai_coach_rate_limit_reservations"
    __table_args__ = (
        UniqueConstraint(
            "scope",
            "subject_hash",
            "window_start",
            "slot",
            name="uq_ai_coach_rate_limit_slot",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    scope: Mapped[str] = mapped_column(String(8))
    subject_hash: Mapped[str] = mapped_column(String(64))
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    slot: Mapped[int] = mapped_column(Integer)
    request_id: Mapped[str] = mapped_column(String(36), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
