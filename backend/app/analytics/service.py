from datetime import date, timedelta
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    AnalyticsSummary,
    CalorieDay,
    MacroAchievement,
    PregnancyAnalyticsSummary,
    WeightPoint,
)
from app.auth.models import User
from app.foods.models import Food
from app.meals.models import MealEntry
from app.profiles.models import BodyProfile
from app.weights.models import WeightEntry


def build_weight_points(weights) -> list[WeightPoint]:
    points = []
    values: list[float] = []
    for item in weights:
        values.append(float(item.weight_kg))
        points.append(
            WeightPoint(
                date=item.recorded_date,
                weight_kg=values[-1],
                moving_average_7d=round(mean(values[-7:]), 2),
            )
        )
    return points


def build_pregnancy_summary(
    session: Session, user_id: str, period: int, end_date: date
) -> PregnancyAnalyticsSummary:
    start = end_date - timedelta(days=period - 1)
    meals = session.scalars(
        select(MealEntry).where(
            MealEntry.subject_user_id == user_id,
            MealEntry.meal_date.between(start, end_date),
        )
    ).all()
    weights = session.scalars(
        select(WeightEntry)
        .where(
            WeightEntry.subject_user_id == user_id,
            WeightEntry.recorded_date.between(start, end_date),
        )
        .order_by(WeightEntry.recorded_date)
    ).all()
    food_ids = {meal.food_id for meal in meals}
    categories = set()
    if food_ids:
        categories = set(
            session.scalars(select(Food.food_group).where(Food.id.in_(food_ids))).all()
        )
    recorded_days = len({meal.meal_date for meal in meals})
    points = build_weight_points(weights)
    facts = [
        f"本周期记录饮食 {recorded_days} 天",
        f"覆盖 {len(categories)} 个食物类别",
    ]
    insight = "已有多次体重记录，可结合产检建议持续观察。" if len(points) >= 2 else None
    return PregnancyAnalyticsSummary(
        period=period,
        weight_points=points,
        recorded_day_count=recorded_days,
        food_category_diversity=len(categories),
        facts=facts,
        insight=insight,
    )


def build_summary(
    session: Session, user_id: str, period: int, end_date: date
) -> AnalyticsSummary | PregnancyAnalyticsSummary:
    user = session.get(User, user_id)
    if user is not None and user.product_mode == "pregnancy":
        return build_pregnancy_summary(session, user_id, period, end_date)
    start = end_date - timedelta(days=period - 1)
    meals = session.scalars(select(MealEntry).where(MealEntry.user_id == user_id, MealEntry.meal_date.between(start, end_date))).all()
    weights = session.scalars(select(WeightEntry).where(WeightEntry.user_id == user_id, WeightEntry.recorded_date.between(start, end_date)).order_by(WeightEntry.recorded_date)).all()
    profile = session.scalar(select(BodyProfile).where(BodyProfile.user_id == user_id))
    calorie_by_date = {start + timedelta(days=i): 0.0 for i in range(period)}
    for meal in meals:
        calorie_by_date[meal.meal_date] += float(meal.energy_kcal)
    calorie_days = [CalorieDay(date=day, consumed_kcal=round(value, 2), budget_kcal=profile.daily_kcal if profile else None) for day, value in calorie_by_date.items()]
    points = build_weight_points(weights)
    protein = sum(float(item.protein_g) for item in meals)
    carbs = sum(float(item.carbohydrate_g) for item in meals)
    fat = sum(float(item.fat_g) for item in meals)
    divisor = max(1, period)
    macros = MacroAchievement(
        protein_percent=round(protein / (profile.protein_g * divisor) * 100, 1) if profile else 0,
        carbohydrate_percent=round(carbs / (profile.carbohydrate_g * divisor) * 100, 1) if profile else 0,
        fat_percent=round(fat / (profile.fat_g * divisor) * 100, 1) if profile else 0,
    )
    insight = "记录正在形成趋势，继续保持。" if meals or weights else None
    return AnalyticsSummary(period=period, weight_points=points, calorie_days=calorie_days, macro_achievement=macros, insight=insight)
