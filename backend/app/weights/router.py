from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import get_current_user
from app.db.session import get_session
from app.pregnancies.service import get_active_episode
from app.weights.models import WeightEntry


class WeightCreate(BaseModel):
    recorded_date: date
    weight_kg: Decimal = Field(ge=30, le=300)
    subject_user_id: str | None = Field(default=None, min_length=1, max_length=36)


class WeightRead(WeightCreate):
    id: str
    pregnancy_episode_id: str | None
    subject_user_id: str | None
    created_by_user_id: str | None


router = APIRouter(prefix="/api/v1/weights", tags=["weights"])


@router.post("", response_model=WeightRead)
def upsert_weight(body: WeightCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> WeightEntry:
    subject_user_id = body.subject_user_id or current_user.id
    if subject_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="尚未获得为该用户记录的权限")
    episode = get_active_episode(session, subject_user_id)
    entry = session.scalar(
        select(WeightEntry).where(
            WeightEntry.user_id == subject_user_id,
            WeightEntry.recorded_date == body.recorded_date,
        )
    )
    if entry is None:
        entry = WeightEntry(
            user_id=subject_user_id,
            pregnancy_episode_id=episode.id if episode is not None else None,
            subject_user_id=subject_user_id,
            created_by_user_id=current_user.id,
            recorded_date=body.recorded_date,
            weight_kg=body.weight_kg,
        )
    else:
        entry.weight_kg = body.weight_kg
        entry.pregnancy_episode_id = episode.id if episode is not None else entry.pregnancy_episode_id
        entry.subject_user_id = subject_user_id
        entry.created_by_user_id = current_user.id
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry
