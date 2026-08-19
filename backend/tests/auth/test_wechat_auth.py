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
