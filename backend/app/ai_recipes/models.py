from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AiRecommendationSession(Base):
    __tablename__ = "ai_recommendation_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filters: Mapped[dict] = mapped_column(JSON, default=dict)
    query_text: Mapped[str] = mapped_column(Text, default="")
    displayed_fingerprints: Mapped[list[str]] = mapped_column(JSON, default=list)
    candidates: Mapped[list[dict]] = mapped_column(JSON, default=list)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AiRecipeRequestEvent(Base):
    __tablename__ = "ai_recipe_request_events"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_ai_recipe_event_user_idempotency"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        ForeignKey("ai_recommendation_sessions.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    request_kind: Mapped[str] = mapped_column(String(16))
    request_ip_hash: Mapped[str] = mapped_column(String(64), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    response_payload: Mapped[dict] = mapped_column(JSON)
    provider_call_count: Mapped[int] = mapped_column(Integer, default=0)
    provider_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    fallback_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
