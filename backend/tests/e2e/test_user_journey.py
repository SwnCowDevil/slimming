from pathlib import Path


PROFILE = {
    "goal": "lose",
    "sex": "female",
    "age": 32,
    "height_cm": 168,
    "current_weight_kg": 72,
    "target_weight_kg": 64,
    "activity_level": "light",
    "dietary_preferences": [],
    "allergens": [],
    "eating_out_frequency": "sometimes",
}


def test_wechat_user_can_complete_core_tracking_journey(client):
    first_login = client.post("/api/v1/auth/wechat", json={"code": "first"}).json()
    second_login = client.post("/api/v1/auth/wechat", json={"code": "second"}).json()
    assert first_login["user_id"] == second_login["user_id"]
    headers = {
        "Authorization": f"Bearer {first_login['access_token']}",
        "X-Admin-Import-Key": "test-admin-import-key",
    }

    profile = client.post("/api/v1/profiles/onboarding", headers=headers, json=PROFILE)
    assert profile.status_code == 201
    assert profile.json()["daily_kcal"] > 0

    fixture = Path(__file__).parents[1] / "foods" / "fixtures" / "tka_sample.json"
    imported = client.post(
        "/api/v1/admin/foods/import",
        headers=headers,
        json={"path": str(fixture), "version": "fixture-2026-08", "dry_run": False},
    )
    assert imported.status_code == 200

    meal = client.post(
        "/api/v1/meals",
        headers={**headers, "Idempotency-Key": "journey-breakfast"},
        json={
            "meal_date": "2026-08-19",
            "meal_type": "breakfast",
            "source_food_id": "8535",
            "grams": 100,
        },
    )
    assert meal.status_code == 200
    assert meal.json()["provider"] == "tka"

    weight = client.post(
        "/api/v1/weights",
        headers=headers,
        json={"recorded_date": "2026-08-19", "weight_kg": 71.6},
    )
    assert weight.status_code == 200

    summary = client.get(
        "/api/v1/analytics/summary?period=7&end_date=2026-08-19", headers=headers
    )
    assert summary.status_code == 200
    assert summary.json()["calorie_days"][-1]["consumed_kcal"] == 162.0
    assert summary.json()["weight_points"][-1]["weight_kg"] == 71.6
