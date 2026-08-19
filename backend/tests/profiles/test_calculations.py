from decimal import Decimal

from app.profiles.schemas import BodyProfileInput
from app.profiles.service import calculate_bmi, calculate_bmr, calculate_targets


def sample_profile(**overrides) -> BodyProfileInput:
    values = {
        "goal": "lose",
        "sex": "female",
        "age": 32,
        "height_cm": Decimal("168"),
        "current_weight_kg": Decimal("82"),
        "target_weight_kg": Decimal("68"),
        "activity_level": "light",
        "dietary_preferences": ["home_cooking"],
        "allergens": [],
        "eating_out_frequency": "sometimes",
    }
    values.update(overrides)
    return BodyProfileInput(**values)


def test_bmi_rounds_to_one_decimal():
    assert calculate_bmi(Decimal("82"), Decimal("168")) == Decimal("29.1")


def test_bmr_uses_mifflin_st_jeor_for_female():
    assert calculate_bmr(sample_profile()) == Decimal("1549")


def test_calorie_target_stays_inside_safe_range():
    target = calculate_targets(sample_profile())

    assert target.minimum_kcal == 1200
    assert target.minimum_kcal <= target.daily_kcal <= target.maximum_kcal
    assert target.protein_g > 0
    assert target.carbohydrate_g > 0
    assert target.fat_g > 0


def test_rejects_target_weight_above_current_for_weight_loss():
    try:
        sample_profile(target_weight_kg=Decimal("90"))
    except ValueError as exc:
        assert "目标体重" in str(exc)
    else:
        raise AssertionError("invalid target weight was accepted")
