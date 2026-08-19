from pathlib import Path

from app.ai_coach.schemas import AiContext
from app.ai_coach.safety import evaluate_safety


def test_pregnancy_context_routes_to_professional():
    result = evaluate_safety(AiContext(pregnancy=True))

    assert result.action == "refer_professional"


def test_ai_draft_does_not_create_meal_before_confirmation(client, auth_headers):
    fixture = Path(__file__).parents[1] / "foods" / "fixtures" / "tka_sample.json"
    client.post(
        "/api/v1/admin/foods/import",
        headers=auth_headers,
        json={"path": str(fixture), "version": "fixture-2026-08", "dry_run": False},
    )
    draft = client.post(
        "/api/v1/ai/drafts",
        headers=auth_headers,
        json={
            "kind": "meal_candidate",
            "meal_date": "2026-08-19",
            "meal_type": "breakfast",
            "source_food_id": "8535",
            "grams": 150,
            "context": {"pregnancy": False},
        },
    )

    assert draft.status_code == 201
    assert draft.json()["status"] == "draft"
    assert client.get("/api/v1/meals?date=2026-08-19", headers=auth_headers).json()["items"] == []

    confirmed = client.post(
        f"/api/v1/ai/drafts/{draft.json()['id']}/confirm",
        headers={**auth_headers, "Idempotency-Key": "ai-draft-confirm"},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"
    assert len(client.get("/api/v1/meals?date=2026-08-19", headers=auth_headers).json()["items"]) == 1
