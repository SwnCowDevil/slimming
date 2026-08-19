from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.foods.models import Food
from app.meals.models import MealEntry
from app.meals.schemas import MealEntryCreate


def create_meal_entry(
    session: Session,
    user_id: str,
    command: MealEntryCreate,
    idempotency_key: str,
) -> MealEntry:
    existing = session.scalar(
        select(MealEntry).where(MealEntry.user_id == user_id, MealEntry.idempotency_key == idempotency_key)
    )
    if existing is not None:
        return existing
    food = session.scalar(select(Food).where(Food.provider == "tka", Food.source_food_id == command.source_food_id))
    if food is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到食物")
    ratio = command.grams / Decimal("100")
    entry = MealEntry(
        user_id=user_id,
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
    session.commit()
    session.refresh(entry)
    return entry

