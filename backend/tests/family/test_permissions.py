from datetime import date, timedelta


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


def test_invitation_acceptance_defaults_and_revocation(client, auth_headers, wechat_gateway):
    pregnancy = create_pregnancy(client, auth_headers)
    owner_id = pregnancy["user_id"]
    invitation = client.post("/api/v1/family/invitations", headers=auth_headers).json()

    assert invitation["token"]
    assert "token_hash" not in invitation

    partner_id, partner_headers = login_as(client, wechat_gateway, "partner-openid")
    accepted = client.post(
        "/api/v1/family/invitations/accept",
        headers=partner_headers,
        json={"token": invitation["token"]},
    )

    assert accepted.status_code == 200
    membership = accepted.json()
    assert membership["owner_user_id"] == owner_id
    assert membership["member_user_id"] == partner_id
    assert membership["permission_scopes"] == ["pregnancy:read", "meal:read"]

    repeated = client.post(
        "/api/v1/family/invitations/accept",
        headers=partner_headers,
        json={"token": invitation["token"]},
    )
    assert repeated.status_code == 409

    owner_members = client.get("/api/v1/family/members", headers=auth_headers)
    assert owner_members.status_code == 200
    assert owner_members.json()["items"][0]["member_user_id"] == partner_id

    revoked = client.delete(
        f"/api/v1/family/members/{membership['id']}",
        headers=auth_headers,
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"


def test_owner_cannot_accept_own_invitation(client, auth_headers):
    create_pregnancy(client, auth_headers)
    invitation = client.post("/api/v1/family/invitations", headers=auth_headers).json()

    response = client.post(
        "/api/v1/family/invitations/accept",
        headers=auth_headers,
        json={"token": invitation["token"]},
    )

    assert response.status_code == 422
