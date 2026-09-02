from pathlib import Path


PROFILE = {
    "goal": "lose", "sex": "female", "age": 32, "height_cm": 168,
    "current_weight_kg": 82, "target_weight_kg": 68, "activity_level": "light",
    "dietary_preferences": [], "allergens": [], "eating_out_frequency": "sometimes"
}


def test_period_summary_contains_weight_calories_and_macros(client, auth_headers):
    fixture = Path(__file__).parents[1] / "foods" / "fixtures" / "tka_sample.json"
    client.post("/api/v1/profiles/onboarding", headers=auth_headers, json=PROFILE)
    client.post(
        "/api/v1/admin/foods/import", headers=auth_headers,
        json={"path": str(fixture), "version": "fixture-2026-08", "dry_run": False}
    )
    client.post(
        "/api/v1/meals", headers={**auth_headers, "Idempotency-Key": "summary-meal"},
        json={"meal_date": "2026-08-19", "meal_type": "breakfast", "source_food_id": "8535", "grams": 150}
    )
    client.post("/api/v1/weights", headers=auth_headers, json={"recorded_date": "2026-08-19", "weight_kg": 68.2})

    response = client.get("/api/v1/analytics/summary?period=7&end_date=2026-08-19", headers=auth_headers)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["period"] == 7
    assert payload["calorie_days"][-1]["consumed_kcal"] == 243.0
    assert payload["weight_points"][-1]["weight_kg"] == 68.2
    assert payload["weight_points"][-1]["moving_average_7d"] == 68.2


def test_summary_rejects_unsupported_period(client, auth_headers):
    assert client.get("/api/v1/analytics/summary?period=14", headers=auth_headers).status_code == 422
