from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "tiny-company-api"


def test_root_endpoint_returns_ok() -> None:
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
