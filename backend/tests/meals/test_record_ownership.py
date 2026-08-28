from datetime import date, timedelta
from pathlib import Path


FIXTURE = Path(__file__).parents[1] / "foods" / "fixtures" / "tka_sample.json"


def prepare_pregnancy_user(client, auth_headers) -> tuple[str, str]:
    imported = client.post(
        "/api/v1/admin/foods/import",
        headers=auth_headers,
        json={"path": str(FIXTURE), "version": "fixture-2026-08", "dry_run": False},
    )
    assert imported.status_code == 200
    pregnancy = client.post(
        "/api/v1/pregnancies",
        headers=auth_headers,
        json={
            "due_date": (date.today() + timedelta(days=112)).isoformat(),
            "height_cm": 168,
            "current_weight_kg": 63,
            "activity_level": "light",
        },
    ).json()
    schedule = client.get("/api/v1/meal-schedules", headers=auth_headers).json()[0]
    return pregnancy["id"], schedule["id"]


def test_self_recorded_meal_tracks_owner_actor_episode_and_schedule(client, auth_headers):
    episode_id, schedule_id = prepare_pregnancy_user(client, auth_headers)

    response = client.post(
        "/api/v1/meals",
        headers={**auth_headers, "Idempotency-Key": "pregnancy-breakfast"},
        json={
            "meal_date": date.today().isoformat(),
            "meal_type": "breakfast",
            "meal_schedule_id": schedule_id,
            "source_food_id": "8535",
            "grams": 100,
            "note": "吃完了",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["subject_user_id"] == body["created_by_user_id"]
    assert body["pregnancy_episode_id"] == episode_id
    assert body["meal_schedule_id"] == schedule_id
    assert body["meal_name_snapshot"] == "早餐"
    assert body["note"] == "吃完了"
    assert body["energy_kcal"] == "162.00"


def test_meal_for_another_subject_is_denied_without_family_permission(client, auth_headers):
    _, schedule_id = prepare_pregnancy_user(client, auth_headers)

    response = client.post(
        "/api/v1/meals",
        headers={**auth_headers, "Idempotency-Key": "unauthorized-subject"},
        json={
            "meal_date": date.today().isoformat(),
            "meal_type": "breakfast",
            "meal_schedule_id": schedule_id,
            "source_food_id": "8535",
            "grams": 100,
            "subject_user_id": "another-user-id",
        },
    )

    assert response.status_code == 403


def test_self_recorded_weight_tracks_owner_actor_and_episode(client, auth_headers):
    episode_id, _ = prepare_pregnancy_user(client, auth_headers)

    response = client.post(
        "/api/v1/weights",
        headers=auth_headers,
        json={"recorded_date": (date.today() + timedelta(days=1)).isoformat(), "weight_kg": 63.4},
    )

    assert response.status_code == 200
    assert response.json()["subject_user_id"] == response.json()["created_by_user_id"]
    assert response.json()["pregnancy_episode_id"] == episode_id
