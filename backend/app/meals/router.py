from datetime import date

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import get_current_user
from app.db.session import get_session
from app.meals.models import MealEntry
from app.meals.schemas import MealEntryCreate, MealEntryRead, MealList
from app.meals.service import create_meal_entry


router = APIRouter(prefix="/api/v1/meals", tags=["meals"])


@router.post("", response_model=MealEntryRead)
def create_entry(
    body: MealEntryCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> MealEntry:
    return create_meal_entry(session, current_user.id, body, idempotency_key)


@router.get("", response_model=MealList)
def list_entries(
    meal_date: date = Query(alias="date"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> MealList:
    items = session.scalars(
        select(MealEntry).where(
            MealEntry.subject_user_id == current_user.id,
            MealEntry.meal_date == meal_date,
        )
    ).all()
    return MealList(items=list(items))
