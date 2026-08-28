from pathlib import Path

from app.foods.tka_provider import TkaProvider


FIXTURE = Path(__file__).parent / "fixtures" / "tka_sample.json"


def test_food_search_is_scoped_to_local_imported_catalog(client, auth_headers, db_session):
    # The API test imports through its own endpoint so it uses the same application DB.
    response = client.post(
        "/api/v1/admin/foods/import",
        headers=auth_headers,
        json={"path": str(FIXTURE), "version": "fixture-2026-08", "dry_run": False},
    )
    assert response.status_code == 200

    search = client.get("/api/v1/foods/search?q=寒天粉", headers=auth_headers)
    assert search.status_code == 200
    assert search.json()["items"][0]["source_food_id"] == "8535"


def test_food_search_returns_empty_items_for_unknown_food(client, auth_headers):
    response = client.get("/api/v1/foods/search?q=不存在的食物", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"items": [], "catalog_ready": False}


def test_food_search_reports_when_the_local_catalog_has_not_been_imported(client, auth_headers):
    response = client.get("/api/v1/foods/search?q=鸡蛋", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"items": [], "catalog_ready": False}
