from fastapi import APIRouter, Query

from app.api.schemas import FundaLinkResponse
from app.api.services import build_funda_link

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
