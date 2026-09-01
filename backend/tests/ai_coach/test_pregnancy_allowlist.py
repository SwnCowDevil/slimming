from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import func, select

from app.ai_coach.models import AiCoachRateLimitReservation
from app.ai_recipes.provider import AiProviderUnavailable
from app.auth.models import User
from app.auth.service import issue_access_token
from app.db.session import get_session


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


class ReflectionProvider:
    def __init__(self):
        self.requests = []

    def generate_reflection(self, *, period, facts):
        self.requests.append({"period": period, "facts": list(facts)})
        return SimpleNamespace(
            response_text="这 7 天已记录 2 天饮食。先保持规律记录，再结合产检建议观察变化。",
            model="fake-deepseek",
            prompt_version="pregnancy-reflection-test-v1",
        )


class UnavailableReflectionProvider:
    def generate_reflection(self, *, period, facts):
        raise AiProviderUnavailable("test outage")


def test_weekly_reflection_uses_ai_with_only_server_summary_facts(client, auth_headers):
    create_pregnancy(client, auth_headers)
    fixture = Path(__file__).parents[1] / "foods" / "fixtures" / "tka_sample.json"
    client.post(
        "/api/v1/admin/foods/import",
        headers=auth_headers,
        json={"path": str(fixture), "version": "fixture-reflection", "dry_run": False},
    )
    client.post(
        "/api/v1/meals",
        headers={**auth_headers, "Idempotency-Key": "historical-reflection-meal"},
        json={
            "meal_date": "2026-08-19",
            "meal_type": "breakfast",
            "source_food_id": "8535",
            "grams": 100,
        },
    )
    provider = ReflectionProvider()
    client.app.state.ai_recipe_provider = provider

    response = client.post(
        "/api/v1/ai/weekly-reflections",
        headers=auth_headers,
        json={"period": 7, "end_date": "2026-08-19", "context": {"pregnancy": True}},
    )

    assert response.status_code == 201
    assert response.json()["response_text"].startswith("这 7 天")
    assert response.json()["model_name"] == "fake-deepseek"
    assert provider.requests == [
        {"period": 7, "facts": ["本周期记录饮食 1 天", "覆盖 1 个食物类别"]}
    ]


def test_weekly_reflection_falls_back_to_server_facts_when_ai_is_unavailable(client, auth_headers):
    create_pregnancy(client, auth_headers)
    client.app.state.ai_recipe_provider = UnavailableReflectionProvider()

    response = client.post(
        "/api/v1/ai/weekly-reflections",
        headers=auth_headers,
        json={"period": 7, "context": {"pregnancy": True}},
    )

    assert response.status_code == 201
    assert response.json()["response_text"] == "本周期记录饮食 0 天；覆盖 0 个食物类别"
    assert response.json()["model_name"] == "rules-pregnancy-v1"


def test_weekly_reflection_rate_limits_model_calls(client, auth_headers, settings):
    create_pregnancy(client, auth_headers)
    settings.ai_recipe_user_limit_per_hour = 1
    provider = ReflectionProvider()
    client.app.state.ai_recipe_provider = provider

    first = client.post(
        "/api/v1/ai/weekly-reflections",
        headers=auth_headers,
        json={"period": 7, "context": {"pregnancy": True}},
    )
    second = client.post(
        "/api/v1/ai/weekly-reflections",
        headers=auth_headers,
        json={"period": 7, "context": {"pregnancy": True}},
    )

    assert first.status_code == 201
    assert second.status_code == 429
    assert len(provider.requests) == 1

    session_iterator = client.app.dependency_overrides[get_session]()
    session = next(session_iterator)
    reservation_count = session.scalar(
        select(func.count(AiCoachRateLimitReservation.id))
    )
    session.close()
    assert reservation_count == 2


def test_weekly_reflection_rate_limits_shared_client_ip(client, auth_headers, settings):
    create_pregnancy(client, auth_headers)
    settings.ai_recipe_user_limit_per_hour = 20
    settings.ai_recipe_ip_limit_per_hour = 1
    provider = ReflectionProvider()
    client.app.state.ai_recipe_provider = provider
    first = client.post(
        "/api/v1/ai/weekly-reflections",
        headers=auth_headers,
        json={"period": 7, "context": {"pregnancy": True}},
    )

    session_iterator = client.app.dependency_overrides[get_session]()
    session = next(session_iterator)
    second_user = User()
    session.add(second_user)
    session.commit()
    session.refresh(second_user)
    second_headers = {
        "Authorization": f"Bearer {issue_access_token(second_user.id, settings)}"
    }
    session.close()
    create_pregnancy(client, second_headers)
    second = client.post(
        "/api/v1/ai/weekly-reflections",
        headers=second_headers,
        json={"period": 7, "context": {"pregnancy": True}},
    )

    assert first.status_code == 201
    assert second.status_code == 429
    assert len(provider.requests) == 1


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
