from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.family.service import authorize_subject
from app.meal_plans.models import MealPlanDay, MealPlanItem
from app.meal_plans.schemas import MealPlanItemUpdate
from app.pregnancies.models import MealSchedule
from app.pregnancies.service import require_active_episode


def get_or_create_daily_plan(
    session: Session, user_id: str, plan_date: date
) -> MealPlanDay:
    episode = require_active_episode(session, user_id)
    plan = session.scalar(
        select(MealPlanDay)
        .where(
            MealPlanDay.pregnancy_episode_id == episode.id,
            MealPlanDay.plan_date == plan_date,
        )
        .options(selectinload(MealPlanDay.items))
    )
    if plan is not None:
        return plan
    schedules = session.scalars(
        select(MealSchedule)
        .where(
            MealSchedule.pregnancy_episode_id == episode.id,
            MealSchedule.enabled.is_(True),
        )
        .order_by(MealSchedule.position)
    ).all()
    plan = MealPlanDay(
        pregnancy_episode_id=episode.id,
        subject_user_id=user_id,
        plan_date=plan_date,
        items=[
            MealPlanItem(
                meal_schedule_id=schedule.id,
                meal_name_snapshot=schedule.display_name,
                scheduled_time_snapshot=schedule.scheduled_time,
                position=schedule.position,
            )
            for schedule in schedules
        ],
    )
    session.add(plan)
    session.commit()
    return session.scalar(
        select(MealPlanDay)
        .where(MealPlanDay.id == plan.id)
        .options(selectinload(MealPlanDay.items))
    )


def update_plan_item(
    session: Session,
    actor_user_id: str,
    item_id: str,
    body: MealPlanItemUpdate,
) -> MealPlanItem:
    item = session.scalar(
        select(MealPlanItem)
        .where(MealPlanItem.id == item_id)
        .options(selectinload(MealPlanItem.plan_day))
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="餐单项不存在")
    owner_id = item.plan_day.subject_user_id
    if actor_user_id != owner_id:
        authorize_subject(
            session,
            actor_user_id=actor_user_id,
            subject_user_id=owner_id,
            scope="meal_plan:write_for_owner",
        )
    for name, value in body.model_dump(exclude_unset=True).items():
        setattr(item, name, value)
    item.updated_by_user_id = actor_user_id
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
