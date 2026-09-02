from datetime import date, timedelta


def pregnancy_payload() -> dict:
    return {
        "due_date": (date.today() + timedelta(days=112)).isoformat(),
        "due_date_source": "user_entered",
        "height_cm": 168,
        "pre_pregnancy_weight_kg": 58.5,
        "current_weight_kg": 63.2,
        "activity_level": "light",
        "dietary_preferences": ["home_cooking"],
        "allergens": ["peanut"],
        "avoidances": ["raw_food"],
        "disliked_foods": ["celery"],
        "timezone": "Asia/Shanghai",
    }


def test_create_pregnancy_derives_gestation_and_changes_product_mode(client, auth_headers):
    response = client.post("/api/v1/pregnancies", headers=auth_headers, json=pregnancy_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "active"
    assert body["product_mode"] == "pregnancy"
    assert body["gestation"]["week"] == 24
    assert body["gestation"]["day"] == 0
    assert body["preferences"]["current_weight_kg"] == 63.2
    assert body["preferences"]["allergens"] == ["peanut"]


def test_current_pregnancy_returns_same_active_episode(client, auth_headers):
    created = client.post(
        "/api/v1/pregnancies", headers=auth_headers, json=pregnancy_payload()
    ).json()

    response = client.get("/api/v1/pregnancies/current", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["due_date"] == created["due_date"]


def test_user_cannot_create_two_active_pregnancies(client, auth_headers):
    client.post("/api/v1/pregnancies", headers=auth_headers, json=pregnancy_payload())

    response = client.post("/api/v1/pregnancies", headers=auth_headers, json=pregnancy_payload())

    assert response.status_code == 409
    assert response.json()["detail"] == "已存在进行中的孕期档案"


def test_end_pregnancy_does_not_create_postpartum_mode(client, auth_headers):
    client.post("/api/v1/pregnancies", headers=auth_headers, json=pregnancy_payload())

    response = client.post("/api/v1/pregnancies/current/end", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "ended"
    assert response.json()["product_mode"] == "pregnancy"
    assert client.get("/api/v1/pregnancies/current", headers=auth_headers).status_code == 404


def test_due_date_outside_supported_pregnancy_window_is_rejected(client, auth_headers):
    payload = pregnancy_payload()
    payload["due_date"] = (date.today() + timedelta(days=300)).isoformat()

    response = client.post("/api/v1/pregnancies", headers=auth_headers, json=payload)

    assert response.status_code == 422


def test_pregnancy_profile_requires_authentication(client):
    assert client.get("/api/v1/pregnancies/current").status_code == 401
