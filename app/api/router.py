from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import (
    BagPropertyResponse,
    FoundationStabilityResponse,
    FundaLinkResponse,
)
from app.api.services import (
    REGIONAL_FOUNDATION_PROVIDERS,
    BagPropertyNotFoundError,
    build_funda_link,
    lookup_bag_property,
)

api_router = APIRouter()


@api_router.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@api_router.get("/funda-link", response_model=FundaLinkResponse, tags=["properties"])
def get_funda_link(
    address: str = Query(min_length=1, description="Street and house number"),
    postcode: str = Query(
        min_length=6,
        max_length=7,
        pattern=r"^[1-9][0-9]{3}\s?[A-Za-z]{2}$",
        description="Dutch postcode, for example 1012 AB",
    ),
) -> FundaLinkResponse:
    normalized_address = " ".join(address.split())
    normalized_postcode = postcode.upper().replace(" ", "")

    return FundaLinkResponse(
        address=normalized_address,
        postcode=normalized_postcode,
        funda_link=build_funda_link(normalized_address, normalized_postcode),
    )


@api_router.get("/bag/property", response_model=BagPropertyResponse, tags=["properties"])
def get_bag_property(
    address: str = Query(min_length=1, description="Street and house number"),
    postcode: str = Query(
        min_length=6,
        max_length=7,
        pattern=r"^[1-9][0-9]{3}\s?[A-Za-z]{2}$",
        description="Dutch postcode, for example 1012 AB",
    ),
) -> BagPropertyResponse:
    normalized_address = " ".join(address.split())
    normalized_postcode = postcode.upper().replace(" ", "")

    try:
        property_data = lookup_bag_property(normalized_address, normalized_postcode)
    except BagPropertyNotFoundError as error:
        raise HTTPException(status_code=404, detail="Address was not found in BAG") from error

    return BagPropertyResponse(**property_data)


@api_router.get(
    "/foundation-stability",
    response_model=FoundationStabilityResponse,
    tags=["properties"],
)
def get_foundation_stability(
    address: str = Query(min_length=1, description="Street and house number"),
    postcode: str = Query(
        min_length=6,
        max_length=7,
        pattern=r"^[1-9][0-9]{3}\s?[A-Za-z]{2}$",
        description="Dutch postcode, for example 1012 AB",
    ),
    region: str = Query("zaanstad", description="Regional data provider"),
) -> FoundationStabilityResponse:
    normalized_address = " ".join(address.split())
    normalized_postcode = postcode.upper().replace(" ", "")
    provider = REGIONAL_FOUNDATION_PROVIDERS.get(region.lower())
    if provider is None:
        raise HTTPException(status_code=400, detail=f"Unsupported region: {region}")

    try:
        property_data = lookup_bag_property(normalized_address, normalized_postcode)
    except BagPropertyNotFoundError as error:
        raise HTTPException(status_code=404, detail="Address was not found in BAG") from error

    indicators = provider(property_data)
    return FoundationStabilityResponse(
        **property_data,
        region=region.lower(),
        status="indicators_found" if indicators else "not_enough_foundation_info",
        indicators=indicators,
        warning=(
            "These are regional ground and soil indicators, not a structural or engineering "
            "assessment of foundation stability."
        ),
    )


@api_router.get(
    "/risk-info",
    response_model=FoundationStabilityResponse,
    tags=["properties"],
    summary="Get combined property risk information",
)
def get_risk_info(
    address: str = Query(min_length=1, description="Street and house number"),
    postcode: str = Query(
        min_length=6,
        max_length=7,
        pattern=r"^[1-9][0-9]{3}\s?[A-Za-z]{2}$",
        description="Dutch postcode, for example 1012 AB",
    ),
    region: str = Query("zaanstad", description="Regional data provider"),
) -> FoundationStabilityResponse:
    return get_foundation_stability(address=address, postcode=postcode, region=region)
