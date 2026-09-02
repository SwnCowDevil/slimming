from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import get_current_user
from app.db.session import get_session
from app.meal_plans.schemas import MealPlanItemRead, MealPlanItemUpdate, MealPlanRead
from app.meal_plans.service import get_or_create_daily_plan, update_plan_item


router = APIRouter(prefix="/api/v1/meal-plans", tags=["meal-plans"])


@router.get("/{plan_date}", response_model=MealPlanRead)
def get_daily_plan(
    plan_date: date,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return get_or_create_daily_plan(session, current_user.id, plan_date)


@router.patch("/items/{item_id}", response_model=MealPlanItemRead)
def patch_plan_item(
    item_id: str,
    body: MealPlanItemUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return update_plan_item(session, current_user.id, item_id, body)
