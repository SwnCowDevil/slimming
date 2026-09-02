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


@pytest.mark.parametrize(
    "ingredient",
    ["料理酒", "红酒", "啤酒", "生鱼片", "半熟牛排", "鲨鱼", "未巴氏杀菌鲜奶"],
)
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


def test_egg_only_recipe_accepts_explicit_generic_full_cook_requirement():
    candidate = _candidate("鸡蛋", ["鸡蛋打散。", "蛋液炒至凝固。"])
    candidate.cooking_requirements = ["彻底炒熟"]

    result = validate_candidate(candidate, allergens=set(), avoidances=set())

    assert result.allowed is True


def test_single_fish_recipe_accepts_explicit_generic_full_cook_requirement():
    candidate = _candidate("鲈鱼", ["鲈鱼处理干净。", "水开后上锅蒸十分钟。"])
    candidate.cooking_requirements = ["完全蒸熟"]

    result = validate_candidate(candidate, allergens=set(), avoidances=set())

    assert result.allowed is True


def test_generic_full_cook_requirement_does_not_cover_multiple_risky_groups():
    candidate = _candidate("鸡胸肉", ["鸡胸肉和鸡蛋一起下锅。"])
    candidate.ingredients.append(candidate.ingredients[0].model_copy(update={"name_zh": "鸡蛋"}))
    candidate.cooking_requirements = ["彻底炒熟"]

    result = validate_candidate(candidate, allergens=set(), avoidances=set())

    assert result.allowed is False
    assert result.reason == "pregnancy_risk:missing_full_cook_instruction:poultry"


def test_user_allergen_discards_candidate():
    result = validate_candidate(_candidate("花生碎"), allergens={"peanut"}, avoidances=set())

    assert result.allowed is False
    assert result.reason == "allergen:peanut"


def test_user_disliked_food_discards_candidate():
    result = validate_candidate(_candidate("香菜"), allergens=set(), avoidances={"香菜"})

    assert result.allowed is False
    assert result.reason == "avoidance:香菜"


def test_unsafe_ingredient_is_rejected_even_when_step_claims_it_was_cooked():
    result = validate_candidate(
        _candidate("红酒", ["长时间炖煮并声称酒精已经挥发。"]),
        allergens=set(),
        avoidances=set(),
    )

    assert result.allowed is False
    assert result.reason == "pregnancy_risk:alcohol"


def test_each_risky_ingredient_needs_its_own_safe_cooking_instruction():
    candidate = _candidate("鸡肉", ["鸡肉持续加热至中心完全熟透。", "鸡蛋蛋黄保持流心。"])
    candidate.ingredients.append(candidate.ingredients[0].model_copy(update={"name_zh": "鸡蛋"}))

    result = validate_candidate(candidate, allergens=set(), avoidances=set())

    assert result.allowed is False
    assert result.reason == "pregnancy_risk:undercooked_instruction"


def test_raw_oyster_instruction_is_rejected():
    result = validate_candidate(
        _candidate("生蚝", ["生蚝开壳直接食用。"]),
        allergens=set(),
        avoidances=set(),
    )

    assert result.allowed is False


def test_fingerprint_ignores_ingredient_order_and_whitespace():
    first = _candidate("鸡胸肉")
    second = first.model_copy(deep=True)
    second.title = "  家常 鸡肉饭  "
    second.ingredients.append(second.ingredients[0].model_copy(update={"name_zh": "番茄"}))
    first.ingredients.insert(0, first.ingredients[0].model_copy(update={"name_zh": "番茄"}))

    assert recipe_fingerprint(first) == recipe_fingerprint(second)
