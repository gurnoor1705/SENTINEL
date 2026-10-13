
import httpx

BASE_URL = "http://127.0.0.1:8000"


def test_health_endpoint_returns_healthy_status():
    response = httpx.get(f"{BASE_URL}/health", timeout=5.0)

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SENTINEL"


def test_health_endpoint_returns_request_id():
    response = httpx.get(f"{BASE_URL}/health", timeout=5.0)

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")
    assert (
        response.json()["request_id"]
        == response.headers["X-Request-ID"]
    )
