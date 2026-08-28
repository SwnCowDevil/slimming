from datetime import date, timedelta
from pathlib import Path


FIXTURE = Path(__file__).parents[1] / "foods" / "fixtures" / "tka_sample.json"


def create_pregnancy(client, headers):
    response = client.post(
        "/api/v1/pregnancies",
        headers=headers,
        json={
            "due_date": (date.today() + timedelta(days=140)).isoformat(),
            "height_cm": 165,
            "pre_pregnancy_weight_kg": 58,
            "current_weight_kg": 61,
            "activity_level": "moderate",
        },
    )
    assert response.status_code == 201
    return response.json()


def login_as(client, gateway, openid):
    gateway.openid = openid
    payload = client.post("/api/v1/auth/wechat", json={"code": "valid-code"}).json()
    return payload["user_id"], {"Authorization": f"Bearer {payload['access_token']}"}


def test_partner_meal_entry_requires_scope_and_tracks_actor(
    client, auth_headers, wechat_gateway
):
    pregnancy = create_pregnancy(client, auth_headers)
    owner_id = pregnancy["user_id"]
    client.post(
        "/api/v1/admin/foods/import",
        headers=auth_headers,
        json={"path": str(FIXTURE), "version": "fixture-family", "dry_run": False},
    )
    invitation = client.post("/api/v1/family/invitations", headers=auth_headers).json()
    partner_id, partner_headers = login_as(client, wechat_gateway, "partner-meal-openid")
    membership = client.post(
        "/api/v1/family/invitations/accept",
        headers=partner_headers,
        json={"token": invitation["token"]},
    ).json()
    schedule = client.get("/api/v1/meal-schedules", headers=auth_headers).json()[0]
    meal = {
        "meal_date": date.today().isoformat(),
        "meal_type": "breakfast",
        "meal_schedule_id": schedule["id"],
        "source_food_id": "8535",
        "grams": 100,
        "subject_user_id": owner_id,
    }

    denied = client.post(
        "/api/v1/meals",
        headers={**partner_headers, "Idempotency-Key": "partner-denied"},
        json=meal,
    )
    assert denied.status_code == 403

    changed = client.patch(
        f"/api/v1/family/members/{membership['id']}/permissions",
        headers=auth_headers,
        json={
            "permission_scopes": [
                "pregnancy:read",
                "meal:read",
                "meal_entry:write_for_owner",
            ]
        },
    )
    assert changed.status_code == 200

    recorded = client.post(
        "/api/v1/meals",
        headers={**partner_headers, "Idempotency-Key": "partner-allowed"},
        json=meal,
    )
    assert recorded.status_code == 200
    assert recorded.json()["subject_user_id"] == owner_id
    assert recorded.json()["created_by_user_id"] == partner_id

    readable = client.get(
        f"/api/v1/meals?date={date.today().isoformat()}&subject_user_id={owner_id}",
        headers=partner_headers,
    )
    assert readable.status_code == 200
    assert readable.json()["items"][0]["id"] == recorded.json()["id"]

    client.delete(f"/api/v1/family/members/{membership['id']}", headers=auth_headers)
    after_revoke = client.post(
        "/api/v1/meals",
        headers={**partner_headers, "Idempotency-Key": "partner-revoked"},
        json=meal,
    )
    assert after_revoke.status_code == 403
