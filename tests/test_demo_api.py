
import httpx

BASE_URL = "http://127.0.0.1:8000"


def test_list_products_returns_three_products():
    response = httpx.get(
        f"{BASE_URL}/demo/products",
        timeout=5.0,
    )

    assert response.status_code == 200

    data = response.json()
    assert data["count"] == 3
    assert len(data["products"]) == 3


def test_get_existing_product():
    response = httpx.get(
        f"{BASE_URL}/demo/products/1",
        timeout=5.0,
    )

    assert response.status_code == 200

    product = response.json()
    assert product["id"] == 1
    assert product["name"] == "Keyboard"
    assert product["price"] == 1499


def test_missing_product_returns_404():
    response = httpx.get(
        f"{BASE_URL}/demo/products/999",
        timeout=5.0,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product 999 not found"
