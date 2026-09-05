from typing import Any

from pydantic import BaseModel, Field


class FundaLinkResponse(BaseModel):
    address: str
    postcode: str
    funda_link: str = Field(description="Funda search link for the supplied address")


class BagPropertyResponse(FundaLinkResponse):
    bag_addressable_object_id: str
    bag_address_designation_id: str
    street: str
    house_number: int
    city: str


class FoundationIndicator(BaseModel):
    layer: str
    label: str
    details: dict[str, Any] = Field(default_factory=dict)


class FoundationStabilityResponse(BagPropertyResponse):
    region: str
    status: str = Field(
        description="Indicator status, not an engineering assessment of foundation stability"
    )
    indicators: list[FoundationIndicator] = Field(default_factory=list)
    warning: str
