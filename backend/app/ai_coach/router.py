from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_coach.models import AiDraft
from app.ai_coach.safety import evaluate_safety
from app.ai_coach.schemas import AiDraftCreate, AiDraftRead
from app.auth.models import User
from app.auth.service import get_current_user
from app.db.session import get_session
from app.meals.schemas import MealEntryCreate
from app.meals.service import create_meal_entry


router = APIRouter(prefix="/api/v1/ai", tags=["ai-guidance"])


@router.post("/drafts", response_model=AiDraftRead, status_code=201)
def create_draft(
    body: AiDraftCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AiDraft:
    safety = evaluate_safety(body.context)
    if safety.action == "refer_professional":
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
