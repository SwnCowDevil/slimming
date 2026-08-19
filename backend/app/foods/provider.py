from pathlib import Path
from typing import Protocol

from app.foods.schemas import FoodDetail, FoodHit, ImportReport


class FoodCompositionProvider(Protocol):
    def import_dataset(self, path: Path, version: str, dry_run: bool = False) -> ImportReport: ...
    def search(self, query: str, locale: str = "zh-CN", limit: int = 20) -> list[FoodHit]: ...
    def get_food(self, source_food_id: str) -> FoodDetail | None: ...

