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


def test_wellbeing_put_creates_and_updates_one_record_per_day(client, auth_headers):
    create_pregnancy(client, auth_headers)
    day = date.today().isoformat()

    created = client.put(
        f"/api/v1/wellbeing/{day}",
        headers=auth_headers,
        json={"feeling_codes": ["nausea"], "note": "早上明显"},
    )
    updated = client.put(
        f"/api/v1/wellbeing/{day}",
        headers=auth_headers,
        json={"feeling_codes": ["normal"], "note": None},
    )

    assert created.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["id"] == created.json()["id"]
    assert updated.json()["feeling_codes"] == ["normal"]
    assert client.get(f"/api/v1/wellbeing/{day}", headers=auth_headers).json() == updated.json()


def test_unknown_wellbeing_code_is_rejected(client, auth_headers):
    create_pregnancy(client, auth_headers)

    response = client.put(
        f"/api/v1/wellbeing/{date.today().isoformat()}",
        headers=auth_headers,
        json={"feeling_codes": ["diagnosed_condition"]},
    )

    assert response.status_code == 422


def test_missing_wellbeing_record_returns_empty_day(client, auth_headers):
    create_pregnancy(client, auth_headers)
    day = date.today().isoformat()

    response = client.get(f"/api/v1/wellbeing/{day}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["feeling_codes"] == []
    assert response.json()["note"] is None
