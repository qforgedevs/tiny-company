from app.main import health, root


def test_health_endpoint_returns_ok() -> None:
    payload = health()
    assert payload["status"] == "ok"
    assert payload["service"] == "tiny-company-api"


def test_root_endpoint_returns_ok() -> None:
    payload = root()
    assert payload["status"] == "ok"
