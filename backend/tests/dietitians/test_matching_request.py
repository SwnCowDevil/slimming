from app.dietitians.models import Dietitian
from app.db.session import get_session


def test_matching_request_is_scoped_to_logged_in_user(client, auth_headers):
    session_iterator = client.app.dependency_overrides[get_session]()
    session = next(session_iterator)
    session.add(
        Dietitian(
            id="dietitian-1",
            display_name="Lin",
            specialties=["weight-management", "vegetarian"],
            credentials="Registered dietitian",
            bio="Evidence-based nutrition support.",
        )
    )
    session.commit()
    session.close()

    response = client.post(
        "/api/v1/dietitian-requests",
        headers=auth_headers,
        json={"dietitian_id": "dietitian-1", "goal": "weight-management", "note": "Need a weekly plan"},
    )

    assert response.status_code == 201
    assert response.json()["dietitian_id"] == "dietitian-1"
    assert response.json()["status"] == "submitted"
