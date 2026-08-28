from datetime import date, timedelta


def test_same_openid_reuses_internal_user_id(client, wechat_gateway):
    first = client.post("/api/v1/auth/wechat", json={"code": "code-a"})
    second = client.post("/api/v1/auth/wechat", json={"code": "code-b"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["user_id"] == second.json()["user_id"]
    assert first.json()["access_token"]


def test_different_openid_creates_different_internal_user_id(client, wechat_gateway):
    first = client.post("/api/v1/auth/wechat", json={"code": "code-a"}).json()
    wechat_gateway.openid = "openid-456"
    second = client.post("/api/v1/auth/wechat", json={"code": "code-b"}).json()

    assert first["user_id"] != second["user_id"]


def test_invalid_wechat_code_returns_401_without_upstream_details(client):
    response = client.post("/api/v1/auth/wechat", json={"code": "invalid"})

    assert response.status_code == 401
    assert response.json() == {"detail": "微信登录失败，请重试"}


def test_dev_auth_is_not_registered_when_disabled(client):
    response = client.post("/api/v1/auth/dev", json={"user_id": "demo"})

    assert response.status_code == 404


def test_profile_update_is_saved_for_current_internal_user(client):
    login = client.post("/api/v1/auth/wechat", json={"code": "code-a"}).json()
    response = client.patch(
        "/api/v1/auth/me/wechat-profile",
        headers={"Authorization": f"Bearer {login['access_token']}"},
        json={"nickname": "小满", "avatar_url": "https://example.test/avatar.png"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == login["user_id"]
    assert response.json()["nickname"] == "小满"


def test_account_deletion_removes_pregnancy_data_and_invalidates_existing_token(client):
    login = client.post("/api/v1/auth/wechat", json={"code": "code-a"}).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}
    pregnancy = {
        "due_date": (date.today() + timedelta(days=112)).isoformat(),
        "height_cm": 168,
        "current_weight_kg": 63.2,
        "activity_level": "light",
        "timezone": "Asia/Shanghai",
    }
    assert client.post("/api/v1/pregnancies", headers=headers, json=pregnancy).status_code == 201

    response = client.delete("/api/v1/auth/me", headers=headers)

    assert response.status_code == 204
    assert client.get("/api/v1/pregnancies/current", headers=headers).status_code == 401
    replacement = client.post("/api/v1/auth/wechat", json={"code": "code-b"}).json()
    assert replacement["user_id"] != login["user_id"]
    replacement_headers = {"Authorization": f"Bearer {replacement['access_token']}"}
    assert client.get("/api/v1/pregnancies/current", headers=replacement_headers).status_code == 404
