from fastapi.testclient import TestClient

from app.api import router
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


def test_bag_property_returns_property_identity(monkeypatch) -> None:
    def fake_lookup(address: str, postcode: str) -> dict[str, str | int]:
        assert address == "Jonkerplantsoen 13"
        assert postcode == "1508EE"
        return {
            "bag_addressable_object_id": "0363010012111931",
            "bag_address_designation_id": "0363200012113669",
            "street": "Jonkerplantsoen",
            "house_number": 13,
            "city": "Zaandam",
            "address": "Jonkerplantsoen 13",
            "postcode": "1508EE",
            "funda_link": "https://www.funda.nl/zoeken/koop/?q=Jonkerplantsoen+13%2C+1508EE",
        }

    monkeypatch.setattr(router, "lookup_bag_property", fake_lookup)
    response = client.get(
        "/api/bag/property",
        params={"address": " Jonkerplantsoen 13 ", "postcode": "1508 ee"},
    )

    assert response.status_code == 200
    assert response.json()["bag_addressable_object_id"] == "0363010012111931"
    assert response.json()["city"] == "Zaandam"


def test_bag_property_returns_not_found(monkeypatch) -> None:
    def fake_lookup(address: str, postcode: str) -> dict[str, str | int]:
        raise router.BagPropertyNotFoundError

    monkeypatch.setattr(router, "lookup_bag_property", fake_lookup)
    response = client.get(
        "/api/bag/property",
        params={"address": "Unknown Street 1", "postcode": "1012 AB"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Address was not found in BAG"}


def test_foundation_stability_returns_regional_indicators(monkeypatch) -> None:
    monkeypatch.setattr(
        router,
        "lookup_bag_property",
        lambda address, postcode: {
            "bag_addressable_object_id": "0363010012111931",
            "bag_address_designation_id": "0363200012113669",
            "street": "Jonkerplantsoen",
            "house_number": 13,
            "city": "Zaandam",
            "address": "Jonkerplantsoen 13",
            "postcode": "1508EE",
            "funda_link": "https://www.funda.nl/zoeken/koop/?q=Jonkerplantsoen+13%2C+1508EE",
            "latitude": 52.44,
            "longitude": 4.83,
        },
    )
    monkeypatch.setitem(
        router.REGIONAL_FOUNDATION_PROVIDERS,
        "zaanstad",
        lambda property_data: [
            {
                "layer": "geo:bodem_hbb3_dempingen",
                "label": "Historical filled areas",
                "details": {"status": "present"},
            }
        ],
    )

    response = client.get(
        "/api/foundation-stability",
        params={"address": "Jonkerplantsoen 13", "postcode": "1508 EE"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "indicators_found"
    assert response.json()["indicators"][0]["label"] == "Historical filled areas"


def test_foundation_stability_reports_insufficient_information(monkeypatch) -> None:
    monkeypatch.setattr(
        router,
        "lookup_bag_property",
        lambda address, postcode: {
            "bag_addressable_object_id": "0363010012111931",
            "bag_address_designation_id": "0363200012113669",
            "street": "Jonkerplantsoen",
            "house_number": 13,
            "city": "Zaandam",
            "address": "Jonkerplantsoen 13",
            "postcode": "1508EE",
            "funda_link": "https://www.funda.nl/zoeken/koop/?q=Jonkerplantsoen+13%2C+1508EE",
            "latitude": 52.44,
            "longitude": 4.83,
        },
    )
    monkeypatch.setitem(router.REGIONAL_FOUNDATION_PROVIDERS, "zaanstad", lambda _: [])

    response = client.get(
        "/api/foundation-stability",
        params={"address": "Jonkerplantsoen 13", "postcode": "1508 EE"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "not_enough_foundation_info"
    assert response.json()["indicators"] == []


def test_foundation_stability_rejects_unknown_region() -> None:
    response = client.get(
        "/api/foundation-stability",
        params={
            "address": "Jonkerplantsoen 13",
            "postcode": "1508 EE",
            "region": "unknown",
        },
    )

    assert response.status_code == 400


def test_risk_info_combines_property_sources(monkeypatch) -> None:
    monkeypatch.setattr(
        router,
        "get_foundation_stability",
        lambda address, postcode, region: {
            "address": "Jonkerplantsoen 13",
            "postcode": "1508EE",
            "funda_link": "https://www.funda.nl/zoeken/koop/?q=Jonkerplantsoen+13%2C+1508EE",
            "bag_addressable_object_id": "0363010012111931",
            "bag_address_designation_id": "0363200012113669",
            "street": "Jonkerplantsoen",
            "house_number": 13,
            "city": "Zaandam",
            "region": "zaanstad",
            "status": "not_enough_foundation_info",
            "indicators": [],
            "warning": "Not an engineering assessment.",
        },
    )

    response = client.get(
        "/api/risk-info",
        params={"address": "Jonkerplantsoen 13", "postcode": "1508 EE"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["funda_link"].startswith("https://www.funda.nl/")
    assert payload["bag_addressable_object_id"] == "0363010012111931"
    assert payload["status"] == "not_enough_foundation_info"
