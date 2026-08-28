from datetime import date, timedelta
from pathlib import Path


FIXTURE = Path(__file__).parents[1] / "foods" / "fixtures" / "tka_sample.json"


def test_pregnancy_summary_uses_recording_facts_not_calorie_budget(client, auth_headers):
    client.post(
        "/api/v1/pregnancies",
        headers=auth_headers,
        json={
            "due_date": (date.today() + timedelta(days=140)).isoformat(),
            "height_cm": 165,
            "current_weight_kg": 61,
            "activity_level": "light",
        },
    )
    client.post(
        "/api/v1/admin/foods/import",
        headers=auth_headers,
        json={"path": str(FIXTURE), "version": "fixture-analytics", "dry_run": False},
    )
    client.post(
        "/api/v1/meals",
        headers={**auth_headers, "Idempotency-Key": "pregnancy-summary-meal"},
        json={
            "meal_date": date.today().isoformat(),
            "meal_type": "breakfast",
            "source_food_id": "8535",
            "grams": 100,
        },
    )

    response = client.get("/api/v1/analytics/summary?period=7", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["product_mode"] == "pregnancy"
    assert "calorie_days" not in payload
    assert "macro_achievement" not in payload
    assert payload["recorded_day_count"] == 1
    assert payload["food_category_diversity"] == 1
    assert payload["facts"] == ["本周期记录饮食 1 天", "覆盖 1 个食物类别"]
    assert payload["insight"] is None
    assert len(payload["weight_points"]) == 1
