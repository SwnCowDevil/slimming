from datetime import date, timedelta


def create_pregnancy(client, auth_headers) -> None:
    response = client.post(
        "/api/v1/pregnancies",
        headers=auth_headers,
        json={
            "due_date": (date.today() + timedelta(days=112)).isoformat(),
            "height_cm": 168,
            "current_weight_kg": 63,
            "activity_level": "light",
        },
    )
    assert response.status_code == 201


def test_new_pregnancy_has_five_ordered_default_meal_schedules(client, auth_headers):
    create_pregnancy(client, auth_headers)

    response = client.get("/api/v1/meal-schedules", headers=auth_headers)

    assert response.status_code == 200
    assert [(item["code"], item["scheduled_time"]) for item in response.json()] == [
        ("breakfast", "08:00"),
        ("snack_am", "10:30"),
        ("lunch", "12:30"),
        ("snack_pm", "15:30"),
        ("dinner", "18:30"),
    ]


def test_meal_schedule_time_can_be_changed_and_persists(client, auth_headers):
    create_pregnancy(client, auth_headers)
    schedule = client.get("/api/v1/meal-schedules", headers=auth_headers).json()[0]

    updated = client.patch(
        f"/api/v1/meal-schedules/{schedule['id']}",
        headers=auth_headers,
        json={"scheduled_time": "07:45", "display_name": "我的早餐"},
    )

    assert updated.status_code == 200
    assert updated.json()["scheduled_time"] == "07:45"
    assert updated.json()["display_name"] == "我的早餐"
    listed = client.get("/api/v1/meal-schedules", headers=auth_headers).json()
    assert listed[0]["scheduled_time"] == "07:45"


def test_invalid_meal_schedule_time_is_rejected(client, auth_headers):
    create_pregnancy(client, auth_headers)
    schedule = client.get("/api/v1/meal-schedules", headers=auth_headers).json()[0]

    response = client.patch(
        f"/api/v1/meal-schedules/{schedule['id']}",
        headers=auth_headers,
        json={"scheduled_time": "25:10"},
    )

    assert response.status_code == 422


def test_meal_schedules_require_active_pregnancy(client, auth_headers):
    response = client.get("/api/v1/meal-schedules", headers=auth_headers)

    assert response.status_code == 404
