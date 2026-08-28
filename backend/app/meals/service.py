from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.foods.models import Food
from app.family.service import authorize_subject
from app.meals.models import MealEntry
from app.meals.schemas import MealEntryCreate
from app.pregnancies.models import MealSchedule
from app.pregnancies.service import get_active_episode


DEFAULT_MEAL_NAMES = {
    "breakfast": "早餐",
    "lunch": "午餐",
    "dinner": "晚餐",
    "snack": "加餐",
}


def create_meal_entry(
    session: Session,
    user_id: str,
    command: MealEntryCreate,
    idempotency_key: str,
    commit: bool = True,
) -> MealEntry:
    subject_user_id = command.subject_user_id or user_id
    authorized_episode = None
    if subject_user_id != user_id:
        authorized_episode = authorize_subject(
            session,
            actor_user_id=user_id,
            subject_user_id=subject_user_id,
            scope="meal_entry:write_for_owner",
        )
    existing = session.scalar(
        select(MealEntry).where(
            MealEntry.user_id == subject_user_id,
            MealEntry.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        return existing
    food = session.scalar(select(Food).where(Food.provider == "tka", Food.source_food_id == command.source_food_id))
    if food is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到食物")
    episode = authorized_episode or get_active_episode(session, subject_user_id)
    schedule = None
    if command.meal_schedule_id is not None:
        if episode is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="当前没有进行中的孕期档案")
        schedule = session.scalar(
            select(MealSchedule).where(
                MealSchedule.id == command.meal_schedule_id,
                MealSchedule.pregnancy_episode_id == episode.id,
            )
        )
        if schedule is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="用餐时段不属于当前孕期")
    ratio = command.grams / Decimal("100")
    entry = MealEntry(
        user_id=subject_user_id,
        pregnancy_episode_id=episode.id if episode is not None else None,
        subject_user_id=subject_user_id,
        created_by_user_id=user_id,
        meal_schedule_id=schedule.id if schedule is not None else None,
        meal_name_snapshot=(schedule.display_name if schedule is not None else DEFAULT_MEAL_NAMES[command.meal_type]),
        note=command.note,
        meal_date=command.meal_date,
        meal_type=command.meal_type,
        food_id=food.id,
        source_food_id=food.source_food_id,
        food_name=food.name_en,
        grams=command.grams,
        energy_kcal=(food.energy_kcal_100g * ratio).quantize(Decimal("0.01")),
        protein_g=(food.protein_g_100g * ratio).quantize(Decimal("0.01")),
        fat_g=(food.fat_g_100g * ratio).quantize(Decimal("0.01")),
        carbohydrate_g=(food.carbohydrate_g_100g * ratio).quantize(Decimal("0.01")),
        fiber_g=(food.fiber_g_100g * ratio).quantize(Decimal("0.01")),
        provider=food.provider,
        dataset_version=food.dataset_version,
        idempotency_key=idempotency_key,
    )
    session.add(entry)
    if commit:
        session.commit()
        session.refresh(entry)
    else:
        session.flush()
    return entry
