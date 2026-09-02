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
    return response.json()


def login_as(client, gateway, openid):
    gateway.openid = openid
    payload = client.post("/api/v1/auth/wechat", json={"code": "valid-code"}).json()
    return payload["user_id"], {"Authorization": f"Bearer {payload['access_token']}"}


def test_partner_task_updates_require_scope_and_record_actor(
    client, auth_headers, wechat_gateway
):
    pregnancy = create_pregnancy(client, auth_headers)
    owner_id = pregnancy["user_id"]
    invitation = client.post("/api/v1/family/invitations", headers=auth_headers).json()
    partner_id, partner_headers = login_as(client, wechat_gateway, "partner-task-openid")
    membership = client.post(
        "/api/v1/family/invitations/accept",
        headers=partner_headers,
        json={"token": invitation["token"]},
    ).json()
    task = client.post(
        "/api/v1/family/tasks",
        headers=auth_headers,
        json={
            "task_date": date.today().isoformat(),
            "task_type": "cooking",
            "title": "准备晚餐",
            "assignee_user_id": partner_id,
        },
    ).json()

    denied = client.patch(
        f"/api/v1/family/tasks/{task['id']}",
        headers=partner_headers,
        json={"status": "completed"},
    )
    assert denied.status_code == 403

    client.patch(
        f"/api/v1/family/members/{membership['id']}/permissions",
        headers=auth_headers,
        json={
            "permission_scopes": [
                "pregnancy:read",
                "meal:read",
                "family_task:write",
            ]
        },
    )
    completed = client.patch(
        f"/api/v1/family/tasks/{task['id']}",
        headers=partner_headers,
        json={"status": "completed"},
    )

    assert completed.status_code == 200
    assert completed.json()["subject_user_id"] == owner_id
    assert completed.json()["completed_by_user_id"] == partner_id
    assert completed.json()["completed_at"]
