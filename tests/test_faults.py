
import time

import httpx

BASE_URL = "http://127.0.0.1:8000"


def clear_faults():
    response = httpx.delete(f"{BASE_URL}/demo/faults", timeout=5.0)
    assert response.status_code == 200


def test_http_503_fault_and_recovery():
    try:
        # The API should work before fault injection.
        baseline = httpx.get(f"{BASE_URL}/demo/products", timeout=5.0)
        assert baseline.status_code == 200

        # Enable the HTTP 503 fault.
        injected = httpx.post(
            f"{BASE_URL}/demo/faults/http-503", timeout=5.0
        )
        assert injected.status_code == 200

        # Confirm the API now returns HTTP 503.
        failed = httpx.get(f"{BASE_URL}/demo/products", timeout=5.0)
        assert failed.status_code == 503
        assert "Injected fault" in failed.json()["detail"]

    finally:
        # Always clear the fault, even if an assertion fails.
        clear_faults()

    # Confirm the API recovers after clearing the fault.
    recovered = httpx.get(f"{BASE_URL}/demo/products", timeout=5.0)
    assert recovered.status_code == 200


def test_latency_fault():
    try:
        # Enable a half-second delay.
        injected = httpx.post(
            f"{BASE_URL}/demo/faults/latency",
            params={"delay_seconds": 0.5},
            timeout=5.0,
        )
        assert injected.status_code == 200

        # Measure the response time.
        start = time.perf_counter()
        response = httpx.get(
            f"{BASE_URL}/demo/products", timeout=5.0
        )
        elapsed = time.perf_counter() - start

        assert response.status_code == 200
        assert elapsed >= 0.45

    finally:
        clear_faults()
