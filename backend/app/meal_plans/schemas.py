from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class MealPlanItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    meal_schedule_id: str
    meal_name_snapshot: str
    scheduled_time_snapshot: str
    position: int
    recipe_id: str | None
    title_snapshot: str | None
    state: str
    assignee_user_id: str | None
    updated_by_user_id: str | None
    updated_at: datetime


class MealPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pregnancy_episode_id: str
    subject_user_id: str
    plan_date: date
    status: str
    rule_version: str
    items: list[MealPlanItemRead]


class MealPlanItemUpdate(BaseModel):
    state: Literal["pending", "preparing", "eaten", "skipped"] | None = None
    recipe_id: str | None = None
    title_snapshot: str | None = None
    assignee_user_id: str | None = None
