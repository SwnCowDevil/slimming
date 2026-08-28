import pytest

from app.ai_recipes.schemas import RecipeCandidate
from app.ai_recipes.validation import recipe_fingerprint, validate_candidate


def _candidate(ingredient: str = "鸡胸肉", steps: list[str] | None = None) -> RecipeCandidate:
    return RecipeCandidate.model_validate(
        {
            "title": "家常鸡肉饭",
            "summary": "清淡家常",
            "meal_type": "dinner",
            "tags": ["home-style"],
            "servings": 1,
            "minutes": 25,
            "ingredients": [
                {
                    "name_zh": ingredient,
                    "quantity": 100,
                    "unit": "克",
                    "grams": 100,
                    "energy_kcal_per_100g": 120,
                    "protein_g_per_100g": 20,
                    "fat_g_per_100g": 3,
                    "carbohydrate_g_per_100g": 2,
                    "fiber_g_per_100g": 0,
                }
            ],
            "steps": steps or ["加热至中心完全熟透后食用。"],
            "allergens": [],
            "nutrition_per_serving": {
                "energy_kcal": 120,
                "protein_g": 20,
                "fat_g": 3,
                "carbohydrate_g": 2,
                "fiber_g": 0,
            },
            "recommendation_reason": "适合家常晚餐",
            "cooking_requirements": ["肉类必须全熟"],
        }
    )


@pytest.mark.parametrize("ingredient", ["料理酒", "生鱼片", "鲨鱼", "未巴氏杀菌鲜奶"])
def test_pregnancy_hard_risk_discards_whole_candidate(ingredient):
    result = validate_candidate(_candidate(ingredient), allergens=set(), avoidances=set())

    assert result.allowed is False
    assert result.normalized_candidate is None


def test_raw_egg_is_rejected_but_fully_cooked_egg_is_allowed():
    raw = validate_candidate(
        _candidate("生鸡蛋", ["打散后拌入米饭直接食用。"]),
        allergens=set(),
        avoidances=set(),
    )
    cooked = validate_candidate(
        _candidate("鸡蛋", ["鸡蛋持续加热至蛋黄和蛋白完全凝固。"]),
        allergens=set(),
        avoidances=set(),
    )

    assert raw.allowed is False
    assert cooked.allowed is True


def test_user_allergen_discards_candidate():
    result = validate_candidate(_candidate("花生碎"), allergens={"peanut"}, avoidances=set())

    assert result.allowed is False
    assert result.reason == "allergen:peanut"


def test_fingerprint_ignores_ingredient_order_and_whitespace():
    first = _candidate("鸡胸肉")
    second = first.model_copy(deep=True)
    second.title = "  家常 鸡肉饭  "
    second.ingredients.append(second.ingredients[0].model_copy(update={"name_zh": "番茄"}))
    first.ingredients.insert(0, first.ingredients[0].model_copy(update={"name_zh": "番茄"}))

    assert recipe_fingerprint(first) == recipe_fingerprint(second)
