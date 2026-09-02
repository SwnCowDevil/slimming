from pathlib import Path


def test_regular_wechat_user_cannot_import_global_food_catalog(client):
    login = client.post("/api/v1/auth/wechat", json={"code": "valid-code"}).json()
    fixture = Path(__file__).parent / "fixtures" / "tka_sample.json"
    response = client.post(
        "/api/v1/admin/foods/import",
        headers={"Authorization": f"Bearer {login['access_token']}"},
        json={"path": str(fixture), "version": "fixture-2026-08", "dry_run": True},
    )

    assert response.status_code == 403
