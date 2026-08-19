from datetime import date
from pydantic import BaseModel


class WeightPoint(BaseModel):
    date: date
    weight_kg: float
    moving_average_7d: float


class CalorieDay(BaseModel):
    date: date
    consumed_kcal: float
    budget_kcal: int | None


class MacroAchievement(BaseModel):
    protein_percent: float
    carbohydrate_percent: float
    fat_percent: float


class AnalyticsSummary(BaseModel):
    period: int
    weight_points: list[WeightPoint]
    calorie_days: list[CalorieDay]
    macro_achievement: MacroAchievement
    insight: str | None

