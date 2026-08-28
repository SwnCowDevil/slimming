import hashlib
import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.foods.schemas import ImportReport
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
        for record in payload.get("recipes", []):
            raw = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            recipe = self.session.scalar(
                select(Recipe).where(Recipe.id == record["id"]).options(selectinload(Recipe.items))
            )
            if (
                recipe is not None
                and recipe.content_fingerprint == fingerprint
                and recipe.content_version == version
            ):
                report.unchanged += 1
                continue
            nutrition = record["nutrition_per_serving"]
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
                "energy_kcal": Decimal(str(nutrition["energy_kcal"])),
                "protein_g": Decimal(str(nutrition["protein_g"])),
                "fat_g": Decimal(str(nutrition["fat_g"])),
                "carbohydrate_g": Decimal(str(nutrition["carbohydrate_g"])),
                "fiber_g": Decimal(str(nutrition["fiber_g"])),
                "source_type": "platform",
                "owner_user_id": None,
                "visibility": "platform",
                "safety_rule_version": record.get("safety_rule_version", "pregnancy-recipe-v1"),
                "nutrition_source": record.get("nutrition_source", "ai_estimated"),
                "nutrition_confidence": record.get("nutrition_confidence", "medium"),
                "content_fingerprint": fingerprint,
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
            for position, ingredient in enumerate(record["ingredients"]):
                recipe.items.append(
                    RecipeItem(
                        ingredient_name_zh=ingredient["name_zh"],
                        original_measure=ingredient["measure"],
                        grams=Decimal(str(ingredient["grams"])),
                        position=position,
                        nutrition_source="ai_estimated",
                        estimated_energy_kcal_per_100g=Decimal(str(ingredient["energy_kcal_per_100g"])),
                        estimated_protein_g_per_100g=Decimal(str(ingredient["protein_g_per_100g"])),
                        estimated_fat_g_per_100g=Decimal(str(ingredient["fat_g_per_100g"])),
                        estimated_carbohydrate_g_per_100g=Decimal(str(ingredient["carbohydrate_g_per_100g"])),
                        estimated_fiber_g_per_100g=Decimal(str(ingredient["fiber_g_per_100g"])),
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
