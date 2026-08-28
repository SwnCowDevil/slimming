import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass

from app.ai_recipes.schemas import RecipeCandidate


SAFETY_RULE_VERSION = "pregnancy-recipe-v1"

FORBIDDEN_TERMS = {
    "料理酒": "alcohol",
    "料酒": "alcohol",
    "黄酒": "alcohol",
    "白酒": "alcohol",
    "米酒": "alcohol",
    "生鱼片": "raw_seafood",
    "刺身": "raw_seafood",
    "生鸡蛋": "raw_egg",
    "溏心蛋": "undercooked_egg",
    "未巴氏杀菌": "unpasteurized_dairy",
    "生乳": "unpasteurized_dairy",
    "鲨鱼": "high_mercury_fish",
    "剑鱼": "high_mercury_fish",
    "方头鱼": "high_mercury_fish",
    "鲭王鱼": "high_mercury_fish",
}

ALLERGEN_ALIASES = {
    "peanut": {"花生", "花生酱", "花生碎"},
    "egg": {"鸡蛋", "鸭蛋", "蛋液", "蛋黄", "蛋白"},
    "milk": {"牛奶", "奶油", "奶酪", "芝士", "酸奶"},
    "shellfish": {"虾", "蟹", "龙虾", "贝"},
    "fish": {"鱼", "三文鱼", "鳕鱼", "鲈鱼"},
    "soy": {"黄豆", "豆腐", "豆浆", "酱油"},
    "wheat": {"小麦", "面粉", "面条", "馒头"},
    "tree_nut": {"核桃", "杏仁", "腰果", "榛子"},
    "sesame": {"芝麻", "芝麻酱"},
}

REQUIRES_FULL_COOKING = {"鸡", "鸭", "猪", "牛", "羊", "肉", "蛋", "鱼", "虾", "蟹", "贝"}
COOKED_TERMS = {"全熟", "熟透", "完全凝固", "中心熟", "彻底加热", "煮沸"}


@dataclass(frozen=True)
class ValidationResult:
    allowed: bool
    reason: str | None
    normalized_candidate: RecipeCandidate | None


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[\W_]+", "", normalized, flags=re.UNICODE)


def _all_text(candidate: RecipeCandidate) -> str:
    return " ".join(
        [candidate.title]
        + [item.name_zh for item in candidate.ingredients]
        + candidate.steps
        + candidate.cooking_requirements
    )


def _matched_allergen(candidate: RecipeCandidate, allergens: set[str]) -> str | None:
    normalized_codes = {normalize_text(code) for code in candidate.allergens}
    ingredient_text = " ".join(item.name_zh for item in candidate.ingredients)
    for allergen in allergens:
        code = normalize_text(allergen)
        if code in normalized_codes:
            return allergen
        aliases = ALLERGEN_ALIASES.get(code, set())
        if any(alias in ingredient_text for alias in aliases):
            return allergen
    return None


def validate_candidate(
    candidate: RecipeCandidate,
    allergens: set[str],
    avoidances: set[str],
) -> ValidationResult:
    text = _all_text(candidate)
    for term, reason in FORBIDDEN_TERMS.items():
        if term in text:
            return ValidationResult(False, f"pregnancy_risk:{reason}", None)

    allergen = _matched_allergen(candidate, allergens)
    if allergen is not None:
        return ValidationResult(False, f"allergen:{allergen}", None)

    normalized_avoidances = {normalize_text(value) for value in avoidances}
    if "rawfood" in normalized_avoidances and any(term in text for term in {"生食", "生拌", "半熟"}):
        return ValidationResult(False, "avoidance:raw_food", None)
    if "alcohol" in normalized_avoidances and "酒" in text:
        return ValidationResult(False, "avoidance:alcohol", None)

    ingredient_text = " ".join(item.name_zh for item in candidate.ingredients)
    if any(term in ingredient_text for term in REQUIRES_FULL_COOKING):
        instructions = " ".join(candidate.steps + candidate.cooking_requirements)
        if not any(term in instructions for term in COOKED_TERMS):
            return ValidationResult(False, "pregnancy_risk:missing_full_cook_instruction", None)

    normalized = candidate.model_copy(deep=True)
    normalized.title = candidate.title.strip()
    normalized.steps = [step.strip() for step in candidate.steps]
    normalized.content_fingerprint = recipe_fingerprint(normalized)
    return ValidationResult(True, None, normalized)


def recipe_fingerprint(candidate: RecipeCandidate) -> str:
    ingredients = sorted(
        (normalize_text(item.name_zh), round(item.grams, 1)) for item in candidate.ingredients
    )
    payload = {
        "title": normalize_text(candidate.title),
        "ingredients": ingredients,
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
