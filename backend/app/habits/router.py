from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import get_current_user
from app.db.session import get_session
from app.habits.models import DailyHabit


class HabitUpdate(BaseModel):
    water_ml: int = Field(ge=0, le=10000)
    steps: int = Field(ge=0, le=200000)


class HabitRead(HabitUpdate):
    habit_date: date


router = APIRouter(prefix="/api/v1/habits", tags=["habits"])


@router.put("/{habit_date}", response_model=HabitRead)
def upsert_habit(habit_date: date, body: HabitUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> DailyHabit:
    entry = session.scalar(select(DailyHabit).where(DailyHabit.user_id == current_user.id, DailyHabit.habit_date == habit_date))
    if entry is None:
        entry = DailyHabit(user_id=current_user.id, habit_date=habit_date)
    entry.water_ml, entry.steps = body.water_ml, body.steps
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.get("/{habit_date}", response_model=HabitRead)
def get_habit(habit_date: date, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> DailyHabit:
    entry = session.scalar(select(DailyHabit).where(DailyHabit.user_id == current_user.id, DailyHabit.habit_date == habit_date))
    return entry or DailyHabit(user_id=current_user.id, habit_date=habit_date, water_ml=0, steps=0)

