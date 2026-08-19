from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


class RecipeItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_food_id: str
    grams: Decimal


class RecipeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    minutes: int
    tags: list[str]
    image_url: str | None
    items: list[RecipeItemRead]


class RecipeRecordRequest(BaseModel):
    meal_date: date
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]


class RecipeRecordResponse(BaseModel):
    recipe_id: str
    meal_entry_ids: list[str]
