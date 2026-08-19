from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import get_current_user
from app.db.session import get_session
from app.weights.models import WeightEntry


class WeightCreate(BaseModel):
    recorded_date: date
    weight_kg: Decimal = Field(ge=30, le=300)


class WeightRead(WeightCreate):
    id: str


router = APIRouter(prefix="/api/v1/weights", tags=["weights"])


@router.post("", response_model=WeightRead)
def upsert_weight(body: WeightCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> WeightEntry:
    entry = session.scalar(select(WeightEntry).where(WeightEntry.user_id == current_user.id, WeightEntry.recorded_date == body.recorded_date))
    if entry is None:
        entry = WeightEntry(user_id=current_user.id, recorded_date=body.recorded_date, weight_kg=body.weight_kg)
    else:
        entry.weight_kg = body.weight_kg
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry

