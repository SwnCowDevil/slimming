from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MealEntryCreate(BaseModel):
    meal_date: date
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    source_food_id: str = Field(min_length=1, max_length=128)
    grams: Decimal = Field(gt=0, le=5000)
    subject_user_id: str | None = Field(default=None, min_length=1, max_length=36)
    meal_schedule_id: str | None = Field(default=None, min_length=1, max_length=36)
    note: str | None = Field(default=None, max_length=500)


class MealEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pregnancy_episode_id: str | None
    subject_user_id: str | None
    created_by_user_id: str | None
    meal_schedule_id: str | None
    meal_name_snapshot: str | None
    recorded_at: datetime
    note: str | None
    meal_date: date
    meal_type: str
    source_food_id: str
    food_name: str
    grams: Decimal
    energy_kcal: Decimal
    protein_g: Decimal
    fat_g: Decimal
    carbohydrate_g: Decimal
    fiber_g: Decimal
    provider: str
    dataset_version: str
    nutrition_source: str
    source_recipe_id: str | None


class MealList(BaseModel):
    items: list[MealEntryRead]
