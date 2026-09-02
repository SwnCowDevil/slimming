from datetime import date
from typing import Literal

from pydantic import BaseModel


class WeightPoint(BaseModel):
    date: date
    weight_kg: float
    moving_average_7d: float


class CalorieDay(BaseModel):
    date: date
    consumed_kcal: float
    budget_kcal: int | None


class PregnancyCalorieDay(BaseModel):
    date: date
    consumed_kcal: float | None


class MacroAchievement(BaseModel):
    protein_percent: float
    carbohydrate_percent: float
    fat_percent: float


class AnalyticsSummary(BaseModel):
    product_mode: Literal["legacy_slimming"] = "legacy_slimming"
    period: int
    weight_points: list[WeightPoint]
    calorie_days: list[CalorieDay]
    macro_achievement: MacroAchievement
    insight: str | None


class PregnancyAnalyticsSummary(BaseModel):
    product_mode: Literal["pregnancy"] = "pregnancy"
    period: int
    weight_points: list[WeightPoint]
    calorie_days: list[PregnancyCalorieDay]
    recorded_day_count: int
    food_category_diversity: int
    facts: list[str]
    insight: str | None
