import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.ai_recipes.models import AiRecommendationSession, AiRecipeRequestEvent
from app.ai_recipes.nutrition import enrich_candidate_nutrition
from app.ai_recipes.provider import AiProviderError, AiRecipeProvider
from app.ai_recipes.schemas import (
    RecommendationBatch,
    RecommendationCreateRequest,
    RecipeGenerationRequest,
)
from app.ai_recipes.validation import validate_candidate
from app.auth.models import User
from app.core.config import Settings
from app.pregnancies.service import derive_gestation, require_active_episode
from app.recipes.schemas import RecipeRead
from app.recipes.service import list_visible_recipes


AI_NOTICE = "AI 推荐仅供饮食安排参考，不替代医生建议。"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_client_ip(client_ip: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), client_ip.encode("utf-8"), hashlib.sha256).hexdigest()


def _stage_for_week(week: int) -> str:
    if week < 14:
        return "first_trimester"
    if week < 28:
        return "second_trimester"
    return "third_trimester"


def _existing_response(session: Session, user_id: str, idempotency_key: str) -> RecommendationBatch | None:
    event = session.scalar(
        select(AiRecipeRequestEvent).where(
            AiRecipeRequestEvent.user_id == user_id,
            AiRecipeRequestEvent.idempotency_key == idempotency_key,
        )
    )
    if event is None or not event.response_payload:
        return None
    return RecommendationBatch.model_validate(event.response_payload)


def _enforce_rate_limit(session: Session, user_id: str, ip_hash: str, settings: Settings) -> None:
    since = utcnow() - timedelta(hours=1)
    user_count = session.scalar(
        select(func.count(AiRecipeRequestEvent.id)).where(
            AiRecipeRequestEvent.user_id == user_id,
            AiRecipeRequestEvent.created_at >= since,
        )
    ) or 0
    ip_count = session.scalar(
        select(func.count(AiRecipeRequestEvent.id)).where(
            AiRecipeRequestEvent.request_ip_hash == ip_hash,
            AiRecipeRequestEvent.created_at >= since,
        )
    ) or 0
    if user_count >= settings.ai_recipe_user_limit_per_hour or ip_count >= settings.ai_recipe_ip_limit_per_hour:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="推荐请求过于频繁，请稍后再试")


def _fallback_candidates(session: Session, user_id: str) -> list[dict]:
    recipes = list_visible_recipes(session, user_id, limit=3)
    return [RecipeRead.model_validate(recipe).model_dump(mode="json") for recipe in recipes]


def _generation_request(
    session: Session,
    user: User,
    body: RecommendationCreateRequest,
    excluded_fingerprints: list[str],
) -> RecipeGenerationRequest:
    episode = require_active_episode(session, user.id)
    gestation = derive_gestation(episode.due_date)
    preferences = episode.preferences
    return RecipeGenerationRequest(
        pregnancy_stage=_stage_for_week(gestation.week),
        allergens=list(preferences.allergens or []),
        avoidances=list(dict.fromkeys([*(preferences.avoidances or []), *(preferences.disliked_foods or [])])),
        filters=body.filters,
        query=body.query,
        excluded_fingerprints=excluded_fingerprints,
    )


def _generate_candidates(
    session: Session,
    provider: AiRecipeProvider,
    request_body: RecipeGenerationRequest,
    settings: Settings,
) -> tuple[list[dict], dict]:
    accepted = []
    excluded = set(request_body.excluded_fingerprints)
    rejected_count = 0
    provider_calls = 0
    last_result = None
    for _attempt in range(settings.ai_max_retries + 1):
        result = provider.generate_recipes(request_body.model_copy(update={"excluded_fingerprints": sorted(excluded)}))
        provider_calls += 1
        last_result = result
        for candidate in result.candidates:
            validation = validate_candidate(candidate, set(request_body.allergens), set(request_body.avoidances))
            if not validation.allowed or validation.normalized_candidate is None:
                rejected_count += 1
                continue
            enriched = enrich_candidate_nutrition(session, validation.normalized_candidate)
            fingerprint = enriched.content_fingerprint
            if fingerprint is None or fingerprint in excluded:
                rejected_count += 1
                continue
            enriched.candidate_id = str(uuid4())
            excluded.add(fingerprint)
            accepted.append(enriched.model_dump(mode="json"))
            if len(accepted) == 3:
                break
        if len(accepted) == 3:
            break
    metadata = {
        "provider_call_count": provider_calls,
        "provider_model": last_result.model if last_result else None,
        "prompt_version": last_result.prompt_version if last_result else None,
        "provider_latency_ms": last_result.latency_ms if last_result else None,
        "input_tokens": last_result.usage.input_tokens if last_result else None,
        "output_tokens": last_result.usage.output_tokens if last_result else None,
        "rejected_count": rejected_count,
    }
    return accepted, metadata


def _finish_event(
    session: Session,
    event: AiRecipeRequestEvent,
    batch: RecommendationBatch,
    metadata: dict,
    fallback_reason: str | None = None,
) -> RecommendationBatch:
    event.response_payload = batch.model_dump(mode="json")
    for field, value in metadata.items():
        setattr(event, field, value)
    event.fallback_reason = fallback_reason
    session.commit()
    return batch


def create_recommendation_session(
    session: Session,
    user: User,
    body: RecommendationCreateRequest,
    idempotency_key: str,
    client_ip: str,
    settings: Settings,
    provider: AiRecipeProvider | None,
) -> RecommendationBatch:
    existing = _existing_response(session, user.id, idempotency_key)
    if existing is not None:
        return existing
    ip_hash = hash_client_ip(client_ip, settings.jwt_secret)
    _enforce_rate_limit(session, user.id, ip_hash, settings)
    expires_at = utcnow() + timedelta(hours=settings.ai_recipe_session_ttl_hours)
    recommendation_session = AiRecommendationSession(
        user_id=user.id,
        filters=body.filters.model_dump(mode="json"),
        query_text=body.query,
        displayed_fingerprints=[],
        candidates=[],
        expires_at=expires_at,
    )
    session.add(recommendation_session)
    session.flush()
    event = AiRecipeRequestEvent(
        session_id=recommendation_session.id,
        user_id=user.id,
        request_kind="initial",
        request_ip_hash=ip_hash,
        idempotency_key=idempotency_key,
        response_payload={},
    )
    session.add(event)
    session.commit()

    if provider is None:
        batch = RecommendationBatch(
            session_id=recommendation_session.id,
            mode="fallback",
            candidates=_fallback_candidates(session, user.id),
            expires_at=expires_at,
            notice=AI_NOTICE,
        )
        return _finish_event(session, event, batch, {}, "provider_disabled")

    request_body = _generation_request(session, user, body, [])
    try:
        candidates, metadata = _generate_candidates(session, provider, request_body, settings)
    except AiProviderError:
        batch = RecommendationBatch(
            session_id=recommendation_session.id,
            mode="fallback",
            candidates=_fallback_candidates(session, user.id),
            expires_at=expires_at,
            notice=AI_NOTICE,
        )
        return _finish_event(session, event, batch, {}, "provider_unavailable")

    recommendation_session.candidates = candidates
    recommendation_session.displayed_fingerprints = [item["content_fingerprint"] for item in candidates]
    batch = RecommendationBatch(
        session_id=recommendation_session.id,
        mode="ai" if candidates else "fallback",
        candidates=candidates or _fallback_candidates(session, user.id),
        expires_at=expires_at,
        notice=AI_NOTICE,
    )
    return _finish_event(session, event, batch, metadata, None if candidates else "no_safe_candidates")


def next_recommendation_batch(
    session: Session,
    user: User,
    session_id: str,
    idempotency_key: str,
    client_ip: str,
    settings: Settings,
    provider: AiRecipeProvider | None,
) -> RecommendationBatch:
    existing = _existing_response(session, user.id, idempotency_key)
    if existing is not None:
        return existing
    recommendation_session = session.scalar(
        select(AiRecommendationSession).where(
            AiRecommendationSession.id == session_id,
            AiRecommendationSession.user_id == user.id,
        )
    )
    now = utcnow()
    if recommendation_session is None or recommendation_session.expires_at.replace(tzinfo=timezone.utc) <= now:
        raise HTTPException(status_code=404, detail="推荐会话已过期，请重新生成")
    ip_hash = hash_client_ip(client_ip, settings.jwt_secret)
    _enforce_rate_limit(session, user.id, ip_hash, settings)
    event = AiRecipeRequestEvent(
        session_id=recommendation_session.id,
        user_id=user.id,
        request_kind="next",
        request_ip_hash=ip_hash,
        idempotency_key=idempotency_key,
        response_payload={},
    )
    session.add(event)
    session.commit()
    body = RecommendationCreateRequest(
        filters=recommendation_session.filters,
        query=recommendation_session.query_text,
    )
    if provider is None:
        batch = RecommendationBatch(
            session_id=session_id,
            mode="fallback",
            candidates=_fallback_candidates(session, user.id),
            expires_at=recommendation_session.expires_at,
            notice=AI_NOTICE,
        )
        return _finish_event(session, event, batch, {}, "provider_disabled")
    request_body = _generation_request(
        session,
        user,
        body,
        list(recommendation_session.displayed_fingerprints),
    )
    try:
        candidates, metadata = _generate_candidates(session, provider, request_body, settings)
    except AiProviderError:
        batch = RecommendationBatch(
            session_id=session_id,
            mode="fallback",
            candidates=_fallback_candidates(session, user.id),
            expires_at=recommendation_session.expires_at,
            notice=AI_NOTICE,
        )
        return _finish_event(session, event, batch, {}, "provider_unavailable")
    recommendation_session.candidates = [*recommendation_session.candidates, *candidates]
    recommendation_session.displayed_fingerprints = [
        *recommendation_session.displayed_fingerprints,
        *[item["content_fingerprint"] for item in candidates],
    ]
    batch = RecommendationBatch(
        session_id=session_id,
        mode="ai" if candidates else "fallback",
        candidates=candidates or _fallback_candidates(session, user.id),
        expires_at=recommendation_session.expires_at,
        notice=AI_NOTICE,
    )
    return _finish_event(session, event, batch, metadata, None if candidates else "no_safe_candidates")


def purge_expired_sessions(session: Session, now: datetime | None = None, limit: int = 500) -> int:
    cutoff = now or utcnow()
    ids = list(
        session.scalars(
            select(AiRecommendationSession.id)
            .where(AiRecommendationSession.expires_at < cutoff)
            .limit(limit)
        )
    )
    if not ids:
        return 0
    session.execute(delete(AiRecommendationSession).where(AiRecommendationSession.id.in_(ids)))
    session.commit()
    return len(ids)
