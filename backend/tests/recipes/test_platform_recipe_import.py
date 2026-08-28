import json
from pathlib import Path

from app.db.session import get_session
from app.recipes.importer import PlatformRecipeImporter


DATASET = Path(__file__).parents[2] / "data" / "imports" / "platform-recipes-v1.json"


def test_platform_dataset_contains_exactly_27_original_recipes():
    payload = json.loads(DATASET.read_text(encoding="utf-8"))

    assert payload["provider"] == "slimming-platform"
    assert payload["version"] == "platform-recipes-v1"
    assert len(payload["recipes"]) == 27
    assert all(item["source_type"] == "platform" for item in payload["recipes"])
    assert all(item["ingredients"] and item["steps"] for item in payload["recipes"])
    assert all(item["image_url"].startswith("/assets/recipes/") for item in payload["recipes"])
    serialized = json.dumps(payload, ensure_ascii=False).casefold()
    assert "themealdb" not in serialized
    assert "http://" not in serialized
    assert "https://" not in serialized


def test_platform_import_is_idempotent_and_preserves_steps(db_session):
    importer = PlatformRecipeImporter(db_session)

    first = importer.import_file(DATASET, "platform-recipes-v1")
    second = importer.import_file(DATASET, "platform-recipes-v1")

    assert first.imported == 27
    assert second.unchanged == 27
    recipe = next(item for item in importer.list_imported() if item.title == "番茄炒蛋")
    assert recipe.steps[0].startswith("番茄")
    assert recipe.items


def test_platform_import_endpoint_requires_admin_key(client, auth_headers, settings):
    settings.tka_import_root = DATASET.parent
    body = {"path": str(DATASET), "version": "platform-recipes-v1", "dry_run": True}

    forbidden = client.post(
        "/api/v1/admin/recipes/import",
        headers={"Authorization": auth_headers["Authorization"]},
        json=body,
    )
    allowed = client.post("/api/v1/admin/recipes/import", headers=auth_headers, json=body)

    assert forbidden.status_code == 403
    assert allowed.status_code == 200
    assert allowed.json()["imported"] == 27
