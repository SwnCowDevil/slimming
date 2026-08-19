from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.profiles.models import BodyProfile
from app.profiles.schemas import BodyProfileInput, NutritionTargets, ProfileRead

ACTIVITY_MULTIPLIERS = {
    "sedentary": Decimal("1.2"),
    "light": Decimal("1.375"),
    "moderate": Decimal("1.55"),
    "active": Decimal("1.725"),
}


def calculate_bmi(weight_kg: Decimal, height_cm: Decimal) -> Decimal:
    metres = height_cm / Decimal("100")
    return (weight_kg / (metres * metres)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def calculate_bmr(profile: BodyProfileInput) -> Decimal:
    offset = Decimal("5") if profile.sex == "male" else Decimal("-161")
    value = (
        Decimal("10") * profile.current_weight_kg
        + Decimal("6.25") * profile.height_cm
        - Decimal("5") * profile.age
        + offset
    )
    return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def calculate_targets(profile: BodyProfileInput) -> NutritionTargets:
    bmi = calculate_bmi(profile.current_weight_kg, profile.height_cm)
    bmr = calculate_bmr(profile)
    maintenance = int((bmr * ACTIVITY_MULTIPLIERS[profile.activity_level]).quantize(Decimal("1")))
    minimum = 1500 if profile.sex == "male" else 1200
    if profile.goal == "lose":
        daily = max(minimum, maintenance - 500)
    else:
        daily = maintenance
    maximum = max(daily, maintenance)
    protein = int((profile.target_weight_kg * Decimal("1.6")).quantize(Decimal("1")))
    fat = max(35, int((Decimal(daily) * Decimal("0.25") / Decimal("9")).quantize(Decimal("1"))))
    carbohydrate = max(80, int(((Decimal(daily) - protein * 4 - fat * 9) / 4).quantize(Decimal("1"))))
    return NutritionTargets(
        bmi=bmi,
        bmr=bmr,
        minimum_kcal=minimum,
        maximum_kcal=maximum,
        daily_kcal=daily,
        protein_g=protein,
        carbohydrate_g=carbohydrate,
        fat_g=fat,
    )


def upsert_profile(session: Session, user_id: str, body: BodyProfileInput) -> BodyProfile:
    targets = calculate_targets(body)
    profile = session.scalar(select(BodyProfile).where(BodyProfile.user_id == user_id))
    if profile is None:
        profile = BodyProfile(user_id=user_id)
    for name, value in body.model_dump().items():
        setattr(profile, name, value)
    for name, value in targets.model_dump().items():
        setattr(profile, name, value)
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def to_profile_read(profile: BodyProfile) -> ProfileRead:
    return ProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        goal=profile.goal,
        sex=profile.sex,
        age=profile.age,
        height_cm=float(profile.height_cm),
        current_weight_kg=float(profile.current_weight_kg),
        target_weight_kg=float(profile.target_weight_kg),
        activity_level=profile.activity_level,
        dietary_preferences=profile.dietary_preferences,
        allergens=profile.allergens,
        eating_out_frequency=profile.eating_out_frequency,
        bmi=float(profile.bmi),
        bmr=float(profile.bmr),
        minimum_kcal=profile.minimum_kcal,
        maximum_kcal=profile.maximum_kcal,
        daily_kcal=profile.daily_kcal,
        protein_g=profile.protein_g,
        carbohydrate_g=profile.carbohydrate_g,
        fat_g=profile.fat_g,
    )

