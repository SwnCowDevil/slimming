from datetime import date, timedelta


def create_pregnancy(client, headers):
    response = client.post(
        "/api/v1/pregnancies",
        headers=headers,
        json={
            "due_date": (date.today() + timedelta(days=140)).isoformat(),
            "height_cm": 165,
            "current_weight_kg": 61,
            "activity_level": "light",
        },
    )
    assert response.status_code == 201


def test_pregnancy_weekly_reflection_is_limited_to_server_facts(client, auth_headers):
    create_pregnancy(client, auth_headers)

    response = client.post(
        "/api/v1/ai/weekly-reflections",
        headers=auth_headers,
        json={"period": 7, "context": {"pregnancy": True}},
    )

    assert response.status_code == 201
    assert response.json()["safety_action"] == "allow_limited"
    assert response.json()["policy_version"] == "pregnancy-allowlist-v1"
    assert set(response.json()["candidate"]) == {"period", "facts"}


def test_serious_symptoms_use_fixed_emergency_guidance(client, auth_headers):
    create_pregnancy(client, auth_headers)

    response = client.post(
        "/api/v1/ai/weekly-reflections",
        headers=auth_headers,
        json={
            "period": 7,
            "context": {"pregnancy": True, "serious_symptoms": True},
        },
    )

    assert response.status_code == 201
    assert response.json()["safety_action"] == "emergency_guidance"
    assert response.json()["model_name"] == "fixed-reviewed-copy"
    assert "及时联系医疗机构" in response.json()["response_text"]


def test_medication_request_refers_and_meal_number_generation_is_rejected(
    client, auth_headers
):
    create_pregnancy(client, auth_headers)
    referred = client.post(
        "/api/v1/ai/weekly-reflections",
        headers=auth_headers,
        json={
            "period": 7,
            "context": {"pregnancy": True, "medication_or_disease": True},
        },
    )
    rejected = client.post(
        "/api/v1/ai/drafts",
        headers=auth_headers,
        json={"kind": "meal_number_generation", "context": {"pregnancy": True}},
    )

    assert referred.status_code == 201
    assert referred.json()["safety_action"] == "refer_professional"
    assert rejected.status_code == 422
