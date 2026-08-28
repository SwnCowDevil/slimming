from datetime import date, timedelta


def create_pregnancy(client, headers):
    response = client.post(
        "/api/v1/pregnancies",
        headers=headers,
        json={
            "due_date": (date.today() + timedelta(days=160)).isoformat(),
            "height_cm": 165,
            "current_weight_kg": 62,
            "activity_level": "light",
        },
    )
    assert response.status_code == 201


def test_daily_plan_materializes_enabled_custom_schedules(client, auth_headers):
    create_pregnancy(client, auth_headers)
    schedules = client.get("/api/v1/meal-schedules", headers=auth_headers).json()
    breakfast = schedules[0]
    client.patch(
        f"/api/v1/meal-schedules/{breakfast['id']}",
        headers=auth_headers,
        json={"display_name": "我的早餐", "scheduled_time": "07:45"},
    )
    client.patch(
        f"/api/v1/meal-schedules/{schedules[1]['id']}",
        headers=auth_headers,
        json={"enabled": False},
    )

    first = client.get(f"/api/v1/meal-plans/{date.today().isoformat()}", headers=auth_headers)
    second = client.get(f"/api/v1/meal-plans/{date.today().isoformat()}", headers=auth_headers)

    assert first.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert len(first.json()["items"]) == 4
    assert first.json()["items"][0]["meal_name_snapshot"] == "我的早餐"
    assert first.json()["items"][0]["scheduled_time_snapshot"] == "07:45"
    assert all(item["recipe_id"] is None for item in first.json()["items"])


def test_plan_item_state_update_records_actor(client, auth_headers):
    create_pregnancy(client, auth_headers)
    plan = client.get(f"/api/v1/meal-plans/{date.today().isoformat()}", headers=auth_headers).json()

    response = client.patch(
        f"/api/v1/meal-plans/items/{plan['items'][0]['id']}",
        headers=auth_headers,
        json={"state": "eaten"},
    )

    assert response.status_code == 200
    assert response.json()["state"] == "eaten"
    assert response.json()["updated_by_user_id"]

