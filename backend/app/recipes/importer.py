import hashlib
import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.foods.schemas import ImportReport
from app.foods.tka_provider import TkaProvider
from app.ai_recipes.validation import recipe_identity_fingerprint
from app.recipes.models import Recipe, RecipeItem


class PlatformRecipeImporter:
    provider_name = "slimming-platform"

    def __init__(self, session: Session) -> None:
        self.session = session

    def import_file(self, path: Path, version: str, dry_run: bool = False) -> ImportReport:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("provider") != self.provider_name:
            raise ValueError("食谱数据提供方必须为 slimming-platform")
        if payload.get("version") != version:
            raise ValueError("食谱数据版本不匹配")
        report = ImportReport()
        tka = TkaProvider(self.session)
        for record in payload.get("recipes", []):
            servings = Decimal(str(record["servings"]))
            prepared = []
            totals = {name: Decimal("0") for name in ("energy_kcal", "protein_g", "fat_g", "carbohydrate_g", "fiber_g")}
            matched_count = 0
            match_signature = []
            for ingredient in record["ingredients"]:
                grams = Decimal(str(ingredient["grams"])) / servings
                food = tka.match_exact(ingredient["name_zh"])
                if food is not None:
                    matched_count += 1
                    source_food_id = food.source_food_id
                    nutrition_source = "tka"
                    nutrient_values = {
                        "energy_kcal": food.energy_kcal_100g,
                        "protein_g": food.protein_g_100g,
                        "fat_g": food.fat_g_100g,
                        "carbohydrate_g": food.carbohydrate_g_100g,
                        "fiber_g": food.fiber_g_100g,
                    }
                    match_signature.append([food.source_food_id, food.dataset_version])
                else:
                    source_food_id = None
                    nutrition_source = "ai_estimated"
                    nutrient_values = {
                        name: Decimal(str(ingredient[f"{name}_per_100g"]))
                        for name in totals
                    }
                    match_signature.append(None)
                ratio = grams / Decimal("100")
                for name, value in nutrient_values.items():
                    totals[name] += value * ratio
                prepared.append((ingredient, grams, source_food_id, nutrition_source, nutrient_values))
            raw = json.dumps(
                {"record": record, "matches": match_signature, "importer": "platform-recipes-v2"},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            import_fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            content_fingerprint = recipe_identity_fingerprint(
                record["title"],
                [(ingredient["name_zh"], float(grams)) for ingredient, grams, *_rest in prepared],
            )
            recipe = self.session.scalar(
                select(Recipe).where(Recipe.id == record["id"]).options(selectinload(Recipe.items))
            )
            if (
                recipe is not None
                and recipe.import_fingerprint == import_fingerprint
                and recipe.content_version == version
            ):
                report.unchanged += 1
                continue
            nutrition_source = (
                "tka" if matched_count == len(prepared) else ("mixed" if matched_count else "ai_estimated")
            )
            values = {
                "title": record["title"],
                "description": record["description"],
                "steps": record["steps"],
                "minutes": record["minutes"],
                "tags": record.get("tags", []),
                "image_url": record["image_url"],
                "content_status": "published",
                "content_version": version,
                "pregnancy_safety": record["pregnancy_safety"],
                "safety_summary": record["safety_summary"],
                "allergen_codes": record.get("allergen_codes", []),
                "subtitle": record.get("subtitle"),
                **{name: value.quantize(Decimal("0.01")) for name, value in totals.items()},
                "source_type": "platform",
                "owner_user_id": None,
                "visibility": "platform",
                "safety_rule_version": record.get("safety_rule_version", "pregnancy-recipe-v1"),
                "nutrition_source": nutrition_source,
                "nutrition_confidence": "high" if nutrition_source == "tka" else ("medium" if nutrition_source == "mixed" else "low"),
                "content_fingerprint": content_fingerprint,
                "import_fingerprint": import_fingerprint,
            }
            if recipe is None:
                recipe = Recipe(id=record["id"], **values)
                self.session.add(recipe)
                report.imported += 1
            else:
                for name, value in values.items():
                    setattr(recipe, name, value)
                recipe.items.clear()
                report.updated += 1
            for position, (ingredient, grams, source_food_id, item_source, nutrients) in enumerate(prepared):
                recipe.items.append(
                    RecipeItem(
                        source_food_id=source_food_id,
                        ingredient_name_zh=ingredient["name_zh"],
                        original_measure=f"每份 {grams:g}克",
                        grams=grams,
                        position=position,
                        nutrition_source=item_source,
                        estimated_energy_kcal_per_100g=nutrients["energy_kcal"],
                        estimated_protein_g_per_100g=nutrients["protein_g"],
                        estimated_fat_g_per_100g=nutrients["fat_g"],
                        estimated_carbohydrate_g_per_100g=nutrients["carbohydrate_g"],
                        estimated_fiber_g_per_100g=nutrients["fiber_g"],
                    )
                )
        if dry_run:
            self.session.rollback()
        else:
            self.session.commit()
        return report

    def list_imported(self) -> list[Recipe]:
        return list(
            self.session.scalars(
                select(Recipe)
                .where(Recipe.source_type == "platform")
                .options(selectinload(Recipe.items))
                .order_by(Recipe.id)
            ).all()
        )
