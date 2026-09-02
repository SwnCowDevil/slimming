def test_daily_habits_upsert_by_user_and_date(client, auth_headers):
    response = client.put(
        "/api/v1/habits/2026-08-19",
        headers=auth_headers,
        json={"water_ml": 1200, "steps": 6400},
    )
    assert response.status_code == 200

    updated = client.put(
        "/api/v1/habits/2026-08-19",
        headers=auth_headers,
        json={"water_ml": 1500, "steps": 7000},
    )
    read = client.get("/api/v1/habits/2026-08-19", headers=auth_headers)

    assert updated.json()["water_ml"] == 1500
    assert read.json()["steps"] == 7000
