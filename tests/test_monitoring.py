import httpx

BASE_URL = "http://127.0.0.1:8000"


def test_request_history_endpoint():
    response = httpx.get(
        f"{BASE_URL}/monitoring/requests",
        params={"limit": 5},
        timeout=5.0,
    )

    assert response.status_code == 200

    data = response.json()
    assert "count" in data
    assert "requests" in data
    assert data["count"] <= 5

    for record in data["requests"]:
        assert "request_id" in record
        assert "method" in record
        assert "path" in record
        assert "status_code" in record
        assert "duration_ms" in record


def test_metrics_endpoint():
    response = httpx.get(
        f"{BASE_URL}/monitoring/metrics",
        timeout=5.0,
    )

    assert response.status_code == 200

    metrics = response.json()

    assert metrics["total_requests"] >= 0
    assert metrics["failed_requests"] >= 0
    assert metrics["failed_requests"] <= metrics["total_requests"]
    assert 0 <= metrics["failure_rate_percent"] <= 100
    assert metrics["avg_response_time_ms"] >= 0


def test_request_history_limit_validation():
    response = httpx.get(
        f"{BASE_URL}/monitoring/requests",
        params={"limit": 101},
        timeout=5.0,
    )

    assert response.status_code == 422
