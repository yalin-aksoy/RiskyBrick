from urllib.parse import urlencode

import httpx

from app.core.config import settings

FUNDA_SEARCH_URL = "https://www.funda.nl/zoeken/koop/"

ZAANSTAD_FOUNDATION_LAYERS = {
    "geo:bodem_hbb3_dempingen": "Historical filled areas",
    "geo:bodem_hbb3_storten_ophogingen": "Historical dumping or raised areas",
    "geo:bodem_bodeminformatie_activiteiten_point": "Soil activity information",
}
ZAANSTAD_FOUNDATION_CARD_LAYER = "geo:zamo_pand_verrijkt"


def build_funda_link(address: str, postcode: str) -> str:
    query = urlencode({"q": f"{address}, {postcode}"})
    return f"{FUNDA_SEARCH_URL}?{query}"


class BagPropertyNotFoundError(ValueError):
    pass


def lookup_bag_property(address: str, postcode: str) -> dict[str, str | int | float]:
    response = httpx.get(
        settings.bag_search_url,
        params={"q": f"{address}, {postcode}", "rows": 10},
        timeout=settings.bag_request_timeout,
    )
    response.raise_for_status()
    documents = response.json().get("response", {}).get("docs", [])

    normalized_postcode = postcode.replace(" ", "").upper()
    property_data = next(
        (
            document
            for document in documents
            if document.get("postcode", "").replace(" ", "").upper() == normalized_postcode
            and document.get("adresseerbaarobject_id")
            and document.get("nummeraanduiding_id")
        ),
        None,
    )
    if property_data is None:
        raise BagPropertyNotFoundError

    return {
        "bag_addressable_object_id": property_data["adresseerbaarobject_id"],
        "bag_address_designation_id": property_data["nummeraanduiding_id"],
        "street": property_data["straatnaam"],
        "house_number": property_data["huisnummer"],
        "city": property_data["woonplaatsnaam"],
        "address": property_data["weergavenaam"].split(",")[0],
        "postcode": normalized_postcode,
        "funda_link": build_funda_link(address, normalized_postcode),
        "latitude": _extract_coordinate(property_data.get("centroide_ll"), 1),
        "longitude": _extract_coordinate(property_data.get("centroide_ll"), 0),
    }


def _extract_coordinate(point: str | None, index: int) -> float:
    if not point or not point.startswith("POINT(") or not point.endswith(")"):
        raise BagPropertyNotFoundError
    coordinates = point[6:-1].split()
    return float(coordinates[index])


def query_zaanstad_foundation(property_data: dict[str, str | int | float]) -> list[dict[str, object]]:
    latitude = float(property_data["latitude"])
    longitude = float(property_data["longitude"])
    indicators = query_zaanstad_foundation_card(property_data)
    for layer, label in ZAANSTAD_FOUNDATION_LAYERS.items():
        response = httpx.get(
            settings.zaanstad_wms_url,
            params={
                "service": "WMS",
                "version": "1.1.1",
                "request": "GetFeatureInfo",
                "layers": layer,
                "query_layers": layer,
                "styles": "",
                "format": "image/png",
                "info_format": "application/json",
                "srs": "EPSG:4326",
                "bbox": f"{longitude - 0.001},{latitude - 0.001},"
                f"{longitude + 0.001},{latitude + 0.001}",
                "width": 101,
                "height": 101,
                "x": 50,
                "y": 50,
                "feature_count": 10,
            },
            timeout=settings.regional_map_request_timeout,
        )
        response.raise_for_status()
        features = response.json().get("features", [])
        for feature in features:
            indicators.append(
                {"layer": layer, "label": label, "details": feature.get("properties", {})}
            )
    return indicators


def query_zaanstad_foundation_card(
    property_data: dict[str, str | int | float],
) -> list[dict[str, object]]:
    latitude = float(property_data["latitude"])
    longitude = float(property_data["longitude"])
    response = httpx.get(
        settings.zaanstad_wfs_url,
        params={
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": ZAANSTAD_FOUNDATION_CARD_LAYER,
            "outputFormat": "application/json",
            "srsName": "EPSG:4326",
            "bbox": f"{longitude - 0.001},{latitude - 0.001},"
            f"{longitude + 0.001},{latitude + 0.001},EPSG:4326",
        },
        timeout=settings.regional_map_request_timeout,
    )
    response.raise_for_status()
    features = response.json().get("features", [])
    address = _normalize_address(str(property_data["address"]))
    matching_features = [
        feature
        for feature in features
        if address
        in {
            _normalize_address(candidate)
            for candidate in str(
                feature.get("properties", {}).get("adressen_in_pand", "")
            ).split(",")
        }
    ]
    if not matching_features:
        matching_features = [
            feature
            for feature in features
            if _point_in_geometry(longitude, latitude, feature.get("geometry"))
        ]

    return [
        {
            "layer": ZAANSTAD_FOUNDATION_CARD_LAYER,
            "label": "Foundation reference card",
            "details": feature.get("properties", {}),
        }
        for feature in matching_features[:1]
    ]


def _normalize_address(address: str) -> str:
    return " ".join(address.casefold().split())


def _point_in_geometry(x: float, y: float, geometry: dict[str, object] | None) -> bool:
    if not geometry:
        return False
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if geometry_type == "Polygon":
        return _point_in_polygon(x, y, coordinates[0])
    if geometry_type == "MultiPolygon":
        return any(_point_in_polygon(x, y, polygon[0]) for polygon in coordinates)
    return False


def _point_in_polygon(x: float, y: float, polygon: list[list[float]]) -> bool:
    inside = False
    previous_x, previous_y = polygon[-1]
    for current_x, current_y in polygon:
        intersects = (current_y > y) != (previous_y > y)
        if intersects and x < (previous_x - current_x) * (y - current_y) / (
            previous_y - current_y
        ) + current_x:
            inside = not inside
        previous_x, previous_y = current_x, current_y
    return inside


REGIONAL_FOUNDATION_PROVIDERS = {"zaanstad": query_zaanstad_foundation}
