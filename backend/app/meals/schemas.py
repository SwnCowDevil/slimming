from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MealEntryCreate(BaseModel):
    meal_date: date
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    source_food_id: str = Field(min_length=1, max_length=128)
    grams: Decimal = Field(gt=0, le=5000)


class MealEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
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


class MealList(BaseModel):
    items: list[MealEntryRead]
