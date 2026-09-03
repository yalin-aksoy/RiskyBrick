from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_service_status() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_check_returns_healthy() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_funda_link_normalizes_address_and_postcode() -> None:
    response = client.get(
        "/api/funda-link",
        params={"address": "  Jonkerplantsoen 13 ", "postcode": "1508 EE"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "address": "Jonkerplantsoen 13",
        "postcode": "1508EE",
        "funda_link": "https://www.funda.nl/zoeken/koop/?q=Jonkerplantsoen+13%2C+1508EE",
    }


def test_funda_link_rejects_invalid_dutch_postcode() -> None:
    response = client.get(
        "/api/funda-link",
        params={"address": "Jonkerplantsoen 13", "postcode": "0000 AA"},
    )

    assert response.status_code == 422
