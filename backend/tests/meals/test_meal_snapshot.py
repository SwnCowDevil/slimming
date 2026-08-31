from datetime import date
from decimal import Decimal
from pathlib import Path

from app.auth.models import User
from app.db.session import get_session
from app.foods.tka_provider import TkaProvider
from app.meals.models import MealEntry
from app.meals.schemas import MealEntryCreate
from app.meals.service import create_meal_entry


FIXTURE = Path(__file__).parents[1] / "foods" / "fixtures" / "tka_sample.json"


def test_meal_snapshot_does_not_change_after_catalog_update(db_session):
    db_session.add(User(id="user-a"))
    db_session.commit()
    provider = TkaProvider(db_session)
    provider.import_dataset(FIXTURE, "fixture-2026-08")
    entry = create_meal_entry(
        db_session,
        user_id="user-a",
        command=MealEntryCreate(
            meal_date=date(2026, 8, 19), meal_type="breakfast", source_food_id="8535", grams=Decimal("150")
        ),
        idempotency_key="meal-a",
    )
    food = provider.get_food("8535")

    assert entry.energy_kcal == Decimal("243.00")
    assert entry.provider == "tka"
    assert entry.dataset_version == "fixture-2026-08"
    assert food.energy_kcal_100g == Decimal("162.00")


def test_duplicate_idempotency_key_returns_same_entry(client, auth_headers):
    fixture = Path(__file__).parents[1] / "foods" / "fixtures" / "tka_sample.json"
    client.post(
        "/api/v1/admin/foods/import",
        headers=auth_headers,
        json={"path": str(fixture), "version": "fixture-2026-08", "dry_run": False},
    )
    body = {"meal_date": "2026-08-19", "meal_type": "breakfast", "source_food_id": "8535", "grams": 150}
    headers = {**auth_headers, "Idempotency-Key": "same-meal"}

    first = client.post("/api/v1/meals", headers=headers, json=body).json()
    second = client.post("/api/v1/meals", headers=headers, json=body).json()

    assert first["id"] == second["id"]
    assert len(client.get("/api/v1/meals?date=2026-08-19", headers=auth_headers).json()["items"]) == 1


def test_meal_api_uses_chinese_alias_for_new_and_existing_tka_records(client, auth_headers):
    client.post(
        "/api/v1/admin/foods/import",
        headers=auth_headers,
        json={"path": str(FIXTURE), "version": "fixture-2026-08", "dry_run": False},
    )
    created = client.post(
        "/api/v1/meals",
        headers={**auth_headers, "Idempotency-Key": "localized-meal"},
        json={
            "meal_date": "2026-08-19",
            "meal_type": "breakfast",
            "source_food_id": "8535",
            "grams": 10,
        },
    )

    assert created.status_code == 200
    assert created.json()["food_name"] == "琼脂"

    session_iterator = client.app.dependency_overrides[get_session]()
    session = next(session_iterator)
    entry = session.get(MealEntry, created.json()["id"])
    assert entry.food_name == "Agar, powder"
    session.close()

    listed = client.get("/api/v1/meals?date=2026-08-19", headers=auth_headers)

    assert listed.status_code == 200
    assert listed.json()["items"][0]["food_name"] == "琼脂"
