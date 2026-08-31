from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai_coach.models import AiCoachRateLimitReservation, AiDraft
from app.ai_coach.safety import evaluate_safety
from app.ai_coach.schemas import AiDraftCreate, AiDraftRead, PregnancyAiRequest
from app.ai_recipes.provider import AiProviderError
from app.ai_recipes.service import hash_client_ip
from app.analytics.service import build_summary
from app.auth.models import User
from app.auth.service import get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.meals.schemas import MealEntryCreate
from app.meals.service import create_meal_entry
from app.recipes.service import list_reviewed_recipes


router = APIRouter(prefix="/api/v1/ai", tags=["ai-guidance"])

POLICY_VERSION = "pregnancy-allowlist-v1"
EMERGENCY_COPY = (
    "当前情况不适合继续使用常规饮食建议，请停止本次操作并及时联系医疗机构；"
    "如情况紧急，请联系当地紧急救助。"
)
REFER_COPY = "该问题涉及药物、疾病或专业医疗判断，请联系产检医生或其他合格医疗专业人员。"


def _claim_rate_limit_slot(
    session: Session,
    *,
    scope: str,
    subject_hash: str,
    window_start: datetime,
    limit: int,
    request_id: str,
) -> None:
    for slot in range(max(0, limit)):
        try:
            with session.begin_nested():
                session.add(
                    AiCoachRateLimitReservation(
                        scope=scope,
                        subject_hash=subject_hash,
                        window_start=window_start,
                        slot=slot,
                        request_id=request_id,
                    )
                )
                session.flush()
            return
        except IntegrityError:
            continue
    raise HTTPException(status_code=429, detail="AI 回顾请求过于频繁，请稍后再试")


def reserve_reflection_rate_limit(
    session: Session,
    user_id: str,
    request_ip_hash: str,
    settings: Settings,
) -> None:
    now = datetime.now(timezone.utc)
    window_start = now.replace(minute=0, second=0, microsecond=0)
    request_id = str(uuid4())
    user_hash = hash_client_ip(user_id, settings.jwt_secret)
    try:
        session.execute(
            delete(AiCoachRateLimitReservation).where(
                AiCoachRateLimitReservation.created_at < now - timedelta(hours=2)
            )
        )
        _claim_rate_limit_slot(
            session,
            scope="user",
            subject_hash=user_hash,
            window_start=window_start,
            limit=settings.ai_recipe_user_limit_per_hour,
            request_id=request_id,
        )
        _claim_rate_limit_slot(
            session,
            scope="ip",
            subject_hash=request_ip_hash,
            window_start=window_start,
            limit=settings.ai_recipe_ip_limit_per_hour,
            request_id=request_id,
        )
        session.commit()
    except Exception:
        session.rollback()
        raise


def create_policy_draft(
    session: Session,
    user_id: str,
    kind: str,
    safety,
    candidate: dict,
    input_data_range: dict,
    response_text: str | None = None,
    model_name: str | None = None,
    prompt_version: str | None = None,
) -> AiDraft:
    if safety.action == "emergency_guidance":
        response_text = EMERGENCY_COPY
        model_name = "fixed-reviewed-copy"
    elif safety.action == "refer_professional":
        response_text = REFER_COPY
        model_name = "fixed-reviewed-copy"
    else:
        model_name = model_name or "rules-pregnancy-v1"
    draft = AiDraft(
        user_id=user_id,
        kind=kind,
        candidate=candidate,
        input_data_range=input_data_range,
        model_name=model_name,
        prompt_version=prompt_version or f"{kind}-v1",
        safety_action=safety.action,
        policy_version=POLICY_VERSION,
        response_text=response_text,
    )
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return draft


@router.post("/drafts", response_model=AiDraftRead, status_code=201)
def create_draft(
    body: AiDraftCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AiDraft:
    safety = evaluate_safety(body.context)
    if safety.action != "allow":
        raise HTTPException(
            status_code=422,
            detail={"action": safety.action, "reason": safety.reason},
        )
    if body.kind == "meal_candidate" and not all(
        [body.meal_date, body.meal_type, body.source_food_id, body.grams]
    ):
        raise HTTPException(status_code=422, detail="meal candidates require date, type, food and grams")
    candidate = body.model_dump(mode="json", exclude={"context", "input_data_range"})
    draft = AiDraft(
        user_id=current_user.id,
        kind=body.kind,
        candidate=candidate,
        input_data_range=body.input_data_range,
        safety_action=safety.action,
    )
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return draft


@router.post("/weekly-reflections", response_model=AiDraftRead, status_code=201)
def create_weekly_reflection(
    body: PregnancyAiRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AiDraft:
    context = body.context.model_copy(update={"pregnancy": True})
    safety = evaluate_safety(context, workflow="weekly_reflection")
    candidate: dict = {}
    input_range = {"period": body.period, "source": "analytics-summary"}
    response_text = None
    if safety.action == "allow_limited":
        client_ip = request.client.host if request.client is not None else "unknown"
        request_ip_hash = hash_client_ip(client_ip, settings.jwt_secret)
        reserve_reflection_rate_limit(session, current_user.id, request_ip_hash, settings)
        summary = build_summary(session, current_user.id, body.period, date.today())
        facts = list(getattr(summary, "facts", []))
        candidate = {"period": body.period, "facts": facts}
        response_text = "；".join(facts) if facts else "本周期暂无足够记录可供回顾。"
        model_name = None
        prompt_version = None
        provider = request.app.state.ai_recipe_provider
        generate = getattr(provider, "generate_reflection", None)
        if callable(generate):
            try:
                generated = generate(period=body.period, facts=facts)
                response_text = generated.response_text
                model_name = generated.model
                prompt_version = generated.prompt_version
            except AiProviderError:
                pass
    else:
        model_name = None
        prompt_version = None
    return create_policy_draft(
        session,
        current_user.id,
        "weekly_reflection",
        safety,
        candidate,
        input_range,
        response_text,
        model_name,
        prompt_version,
    )


@router.post("/recipe-swaps", response_model=AiDraftRead, status_code=201)
def create_recipe_swap(
    body: PregnancyAiRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AiDraft:
    context = body.context.model_copy(update={"pregnancy": True})
    safety = evaluate_safety(context, workflow="recipe_swap")
    candidate: dict = {}
    if safety.action == "allow_limited":
        recipes = list_reviewed_recipes(session, current_user.id, limit=10)
        choices = [
            {
                "id": recipe.id,
                "title": recipe.title,
                "energy_kcal": str(recipe.energy_kcal) if recipe.energy_kcal is not None else None,
                "safety_summary": recipe.safety_summary,
            }
            for recipe in recipes
            if recipe.id != body.current_recipe_id
        ][:3]
        candidate = {"recipe_candidates": choices}
    return create_policy_draft(
        session,
        current_user.id,
        "recipe_swap",
        safety,
        candidate,
        {"source": "reviewed-recipes", "current_recipe_id": body.current_recipe_id},
    )


@router.post("/drafts/{draft_id}/confirm", response_model=AiDraftRead)
def confirm_draft(
    draft_id: str,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AiDraft:
    draft = session.scalar(
        select(AiDraft).where(AiDraft.id == draft_id, AiDraft.user_id == current_user.id)
    )
    if draft is None:
        raise HTTPException(status_code=404, detail="draft not found")
    if draft.status == "confirmed":
        return draft
    if draft.kind != "meal_candidate":
        draft.status = "confirmed"
    else:
        entry = create_meal_entry(
            session,
            current_user.id,
            MealEntryCreate(**{key: draft.candidate[key] for key in [
                "meal_date", "meal_type", "source_food_id", "grams"
            ]}),
            idempotency_key,
        )
        draft.meal_entry_id = entry.id
        draft.status = "confirmed"
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return draft
