PROFILE = {
    "goal": "lose",
    "sex": "female",
    "age": 32,
    "height_cm": 168,
    "current_weight_kg": 82,
    "target_weight_kg": 68,
    "activity_level": "light",
    "dietary_preferences": ["home_cooking"],
    "allergens": ["peanut"],
    "eating_out_frequency": "sometimes",
}


def test_onboarding_creates_profile_for_current_user(client, auth_headers):
    response = client.post("/api/v1/profiles/onboarding", headers=auth_headers, json=PROFILE)

    assert response.status_code == 201
    assert response.json()["bmi"] == 29.1
    assert response.json()["daily_kcal"] >= 1200


def test_read_profile_returns_same_user_data(client, auth_headers):
    created = client.post("/api/v1/profiles/onboarding", headers=auth_headers, json=PROFILE).json()
    response = client.get("/api/v1/profiles/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["target_weight_kg"] == 68.0


def test_profile_requires_authenticated_user(client):
    assert client.get("/api/v1/profiles/me").status_code == 401
