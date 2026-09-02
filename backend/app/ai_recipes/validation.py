import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass

from app.ai_recipes.schemas import RecipeCandidate


SAFETY_RULE_VERSION = "pregnancy-recipe-v2"

FORBIDDEN_TERMS = {
    "料理酒": "alcohol",
    "料酒": "alcohol",
    "黄酒": "alcohol",
    "白酒": "alcohol",
    "米酒": "alcohol",
    "红酒": "alcohol",
    "葡萄酒": "alcohol",
    "啤酒": "alcohol",
    "酒酿": "alcohol",
    "醪糟": "alcohol",
    "朗姆酒": "alcohol",
    "威士忌": "alcohol",
    "生鱼片": "raw_seafood",
    "刺身": "raw_seafood",
    "生鸡蛋": "raw_egg",
    "溏心蛋": "undercooked_egg",
    "温泉蛋": "undercooked_egg",
    "半熟蛋": "undercooked_egg",
    "单面煎蛋": "undercooked_egg",
    "半熟": "undercooked_food",
    "五分熟": "undercooked_food",
    "七分熟": "undercooked_food",
    "生拌": "raw_food",
    "未巴氏杀菌": "unpasteurized_dairy",
    "生乳": "unpasteurized_dairy",
    "未经巴氏杀菌": "unpasteurized_dairy",
    "未经巴氏消毒": "unpasteurized_dairy",
    "未消毒鲜奶": "unpasteurized_dairy",
    "鲨鱼": "high_mercury_fish",
    "剑鱼": "high_mercury_fish",
    "方头鱼": "high_mercury_fish",
    "鲭王鱼": "high_mercury_fish",
    "大耳马鲛": "high_mercury_fish",
    "马林鱼": "high_mercury_fish",
    "旗鱼": "high_mercury_fish",
}

AVOIDANCE_ALIASES = {
    "rawfood": {"生食", "生拌", "刺身", "生鱼片", "半熟", "溏心", "温泉蛋"},
    "alcohol": {"酒", "酒酿", "醪糟"},
    "caffeine": {"咖啡", "浓茶", "能量饮料", "可乐"},
    "spicy": {"辣椒", "辣酱", "麻辣"},
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

COOKED_TERMS = {
    "全熟",
    "熟透",
    "完全凝固",
    "中心熟",
    "彻底加热",
    "煮沸",
    "炒熟",
    "蒸熟",
    "煮熟",
    "烤熟",
    "熟制",
}
UNSAFE_COOKING_TERMS = {
    "流心",
    "蛋黄可流动",
    "蛋液未凝固",
    "夹生",
    "未熟",
    "开壳直接食用",
    "直接生食",
    "直接生吃",
}
FULL_COOK_GROUPS = {
    "poultry": ({"鸡", "鸭", "鹅"}, {"鸡", "鸭", "鹅", "禽肉", "肉类"}),
    "meat": ({"猪", "牛", "羊", "肉"}, {"猪", "牛", "羊", "肉", "肉类"}),
    "egg": ({"蛋"}, {"蛋", "蛋黄", "蛋白", "蛋液"}),
    "fish": ({"鱼"}, {"鱼", "鱼肉", "水产"}),
    "shellfish": ({"虾", "蟹", "贝", "蚝", "牡蛎"}, {"虾", "蟹", "贝", "蚝", "牡蛎", "水产"}),
}


def _ingredient_matches_group(group: str, name: str) -> bool:
    if group == "poultry":
        without_eggs = name.replace("鸡蛋", "").replace("鸭蛋", "").replace("鹅蛋", "")
        return any(alias in without_eggs for alias in ("鸡", "鸭", "鹅", "禽肉"))
    if group == "meat":
        if any(alias in name for alias in ("猪", "牛", "羊")):
            return True
        if "肉" not in name:
            return False
        return not any(alias in name for alias in ("鸡", "鸭", "鹅", "鱼", "虾", "蟹", "贝"))
    ingredient_aliases, _ = FULL_COOK_GROUPS[group]
    return any(alias in name for alias in ingredient_aliases)


def _safe_cooking_instruction(instruction: str) -> bool:
    return any(term in instruction for term in COOKED_TERMS) and not any(
        term in instruction for term in UNSAFE_COOKING_TERMS
    )


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
    if "酒" in text or "醪糟" in text:
        return ValidationResult(False, "pregnancy_risk:alcohol", None)
    for term, reason in FORBIDDEN_TERMS.items():
        if term in text:
            return ValidationResult(False, f"pregnancy_risk:{reason}", None)

    allergen = _matched_allergen(candidate, allergens)
    if allergen is not None:
        return ValidationResult(False, f"allergen:{allergen}", None)

    normalized_text = normalize_text(text)
    for avoidance in avoidances:
        normalized_avoidance = normalize_text(avoidance)
        aliases = AVOIDANCE_ALIASES.get(normalized_avoidance, {avoidance.strip()})
        if normalized_avoidance and any(normalize_text(alias) in normalized_text for alias in aliases):
            return ValidationResult(False, f"avoidance:{normalized_avoidance}", None)

    instructions = candidate.steps + candidate.cooking_requirements
    if any(term in " ".join(instructions) for term in UNSAFE_COOKING_TERMS):
        return ValidationResult(False, "pregnancy_risk:undercooked_instruction", None)
    ingredient_names = [item.name_zh for item in candidate.ingredients]
    active_groups = [
        group
        for group in FULL_COOK_GROUPS
        if any(_ingredient_matches_group(group, name) for name in ingredient_names)
    ]
    generic_requirement_is_safe = len(active_groups) == 1 and any(
        _safe_cooking_instruction(instruction)
        for instruction in candidate.cooking_requirements
    )
    for group in active_groups:
        _, instruction_aliases = FULL_COOK_GROUPS[group]
        has_safe_instruction = any(
            any(alias in instruction for alias in instruction_aliases)
            and _safe_cooking_instruction(instruction)
            for instruction in instructions
        )
        if not has_safe_instruction and not generic_requirement_is_safe:
            return ValidationResult(False, f"pregnancy_risk:missing_full_cook_instruction:{group}", None)

    normalized = candidate.model_copy(deep=True)
    normalized.title = candidate.title.strip()
    normalized.steps = [step.strip() for step in candidate.steps]
    normalized.content_fingerprint = recipe_fingerprint(normalized)
    return ValidationResult(True, None, normalized)


def recipe_fingerprint(candidate: RecipeCandidate) -> str:
    ingredients = [
        (item.name_zh, item.grams / candidate.servings) for item in candidate.ingredients
    ]
    return recipe_identity_fingerprint(candidate.title, ingredients)


def recipe_identity_fingerprint(title: str, ingredients: list[tuple[str, float]]) -> str:
    normalized_ingredients = sorted(
        (normalize_text(name), round(float(grams), 1)) for name, grams in ingredients
    )
    payload = {
        "title": normalize_text(title),
        "ingredients": normalized_ingredients,
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
