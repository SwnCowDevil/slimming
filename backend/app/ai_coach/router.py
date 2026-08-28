from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_coach.models import AiDraft
from app.ai_coach.safety import evaluate_safety
from app.ai_coach.schemas import AiDraftCreate, AiDraftRead, PregnancyAiRequest
from app.analytics.service import build_summary
from app.auth.models import User
from app.auth.service import get_current_user
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


def create_policy_draft(
    session: Session,
    user_id: str,
    kind: str,
    safety,
    candidate: dict,
    input_data_range: dict,
    response_text: str | None = None,
) -> AiDraft:
    if safety.action == "emergency_guidance":
        response_text = EMERGENCY_COPY
        model_name = "fixed-reviewed-copy"
    elif safety.action == "refer_professional":
        response_text = REFER_COPY
        model_name = "fixed-reviewed-copy"
    else:
        model_name = "rules-pregnancy-v1"
    draft = AiDraft(
        user_id=user_id,
        kind=kind,
        candidate=candidate,
        input_data_range=input_data_range,
        model_name=model_name,
        prompt_version=f"{kind}-v1",
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
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AiDraft:
    context = body.context.model_copy(update={"pregnancy": True})
    safety = evaluate_safety(context, workflow="weekly_reflection")
    candidate: dict = {}
    input_range = {"period": body.period, "source": "analytics-summary"}
    response_text = None
    if safety.action == "allow_limited":
        summary = build_summary(session, current_user.id, body.period, date.today())
        facts = list(getattr(summary, "facts", []))
        candidate = {"period": body.period, "facts": facts}
        response_text = "；".join(facts) if facts else "本周期暂无足够记录可供回顾。"
    return create_policy_draft(
        session,
        current_user.id,
        "weekly_reflection",
        safety,
        candidate,
        input_range,
        response_text,
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
