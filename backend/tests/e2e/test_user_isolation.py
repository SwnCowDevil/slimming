from pathlib import Path


def _login(client, code):
    session = client.post("/api/v1/auth/wechat", json={"code": code}).json()
    return {"Authorization": f"Bearer {session['access_token']}"}


def test_meals_and_weights_are_isolated_by_internal_user_id(client, wechat_gateway):
    user_a = _login(client, "a")
    fixture = Path(__file__).parents[1] / "foods" / "fixtures" / "tka_sample.json"
    client.post(
        "/api/v1/admin/foods/import",
        headers={**user_a, "X-Admin-Import-Key": "test-admin-import-key"},
        json={"path": str(fixture), "version": "fixture-2026-08", "dry_run": False},
    )
    client.post(
        "/api/v1/meals",
        headers={**user_a, "Idempotency-Key": "private-meal"},
        json={"meal_date": "2026-08-19", "meal_type": "breakfast", "source_food_id": "8535", "grams": 100},
    )
    client.post("/api/v1/weights", headers=user_a, json={"recorded_date": "2026-08-19", "weight_kg": 70})

    wechat_gateway.openid = "openid-other"
    user_b = _login(client, "b")
    meals = client.get("/api/v1/meals?date=2026-08-19", headers=user_b).json()
    summary = client.get("/api/v1/analytics/summary?period=7&end_date=2026-08-19", headers=user_b).json()

    assert meals["items"] == []
    assert summary["weight_points"] == []
    assert all(day["consumed_kcal"] == 0 for day in summary["calorie_days"])
