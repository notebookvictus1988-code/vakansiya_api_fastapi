from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_contract():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_user_profile_requires_authentication():
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
