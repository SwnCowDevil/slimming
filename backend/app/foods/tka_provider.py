import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.foods.models import Food, FoodAlias
from app.foods.schemas import FoodDetail, FoodHit, ImportReport


class TkaProvider:
    provider_name = "tka"

    def __init__(self, session: Session) -> None:
        self.session = session

    def import_dataset(self, path: Path, version: str, dry_run: bool = False) -> ImportReport:
        if not version.strip():
            raise ValueError("必须提供数据版本")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("provider") != self.provider_name:
            raise ValueError("数据提供方必须为 tka")
        report = ImportReport()
        for record in payload.get("records", []):
            raw = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            raw_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            food = self.session.scalar(
                select(Food).where(
                    Food.provider == self.provider_name,
                    Food.source_food_id == str(record["source_food_id"]),
                )
            )
            if food is not None and food.raw_sha256 == raw_hash and food.dataset_version == version:
                report.unchanged += 1
                continue
            nutrients = record["nutrients_per_100g"]
            values = {
                "provider": self.provider_name,
                "source_food_id": str(record["source_food_id"]),
                "source_url": record["source_url"],
                "foodex2_code": record.get("foodex2_code"),
                "name_en": record["name_en"],
                "name_et": record.get("name_et"),
                "synonyms": record.get("synonyms", []),
                "food_group": record.get("food_group"),
                "source_updated_at": date.fromisoformat(record["source_updated_at"]) if record.get("source_updated_at") else None,
                "household_measures": record.get("household_measures", []),
                "energy_kcal_100g": self._nutrient(nutrients, "energy_kcal"),
                "protein_g_100g": self._nutrient(nutrients, "protein_g"),
                "fat_g_100g": self._nutrient(nutrients, "fat_g"),
                "carbohydrate_g_100g": self._nutrient(nutrients, "carbohydrate_g"),
                "fiber_g_100g": self._nutrient(nutrients, "fiber_g"),
                "salt_g_100g": self._nutrient(nutrients, "salt_g"),
                "method_ids": record.get("method_ids", []),
                "source_ids": record.get("source_ids", []),
                "dataset_version": version,
                "raw_sha256": raw_hash,
            }
            if food is None:
                food = Food(**values)
                self.session.add(food)
                self.session.flush()
                report.imported += 1
            else:
                for name, value in values.items():
                    setattr(food, name, value)
                food.aliases.clear()
                report.updated += 1
            aliases = payload.get("aliases_zh", {}).get(str(record["source_food_id"]), [])
            food.aliases.extend(FoodAlias(locale="zh-CN", name=name) for name in aliases)
        if dry_run:
            self.session.rollback()
        else:
            self.session.commit()
        return report

    def search(self, query: str, locale: str = "zh-CN", limit: int = 20) -> list[FoodHit]:
        term = query.strip()
        if not term:
            return []
        alias_food_ids = select(FoodAlias.food_id).where(FoodAlias.name.ilike(f"%{term}%"))
        foods = self.session.scalars(
            select(Food)
            .where(
                or_(
                    Food.name_en.ilike(f"%{term}%"),
                    Food.name_et.ilike(f"%{term}%"),
                    Food.id.in_(alias_food_ids),
                )
            )
            .limit(min(limit, 50))
        ).all()
        return [self._hit(food, locale) for food in foods]

    def get_food(self, source_food_id: str) -> FoodDetail | None:
        food = self.session.scalar(
            select(Food).where(Food.provider == self.provider_name, Food.source_food_id == source_food_id)
        )
        if food is None:
            return None
        aliases = [alias.name for alias in food.aliases if alias.locale == "zh-CN"]
        return FoodDetail(
            **self._hit(food, "zh-CN").model_dump(),
            provider=food.provider,
            source_url=food.source_url,
            foodex2_code=food.foodex2_code,
            aliases_zh=aliases,
            household_measures=food.household_measures,
            protein_g_100g=food.protein_g_100g,
            fat_g_100g=food.fat_g_100g,
            carbohydrate_g_100g=food.carbohydrate_g_100g,
            fiber_g_100g=food.fiber_g_100g,
            salt_g_100g=food.salt_g_100g,
            dataset_version=food.dataset_version,
        )

    @staticmethod
    def _nutrient(values: dict, key: str) -> Decimal:
        value = Decimal(str(values.get(key, 0)))
        if value < 0:
            raise ValueError(f"营养值不能为负数: {key}")
        return value

    @staticmethod
    def _hit(food: Food, locale: str) -> FoodHit:
        aliases = [alias.name for alias in food.aliases if alias.locale == locale]
        name = aliases[0] if aliases else food.name_en
        return FoodHit(
            id=food.id,
            source_food_id=food.source_food_id,
            name=name,
            energy_kcal_100g=food.energy_kcal_100g,
        )

