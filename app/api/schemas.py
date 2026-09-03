from pydantic import BaseModel, Field


class FundaLinkResponse(BaseModel):
    address: str
    postcode: str
    funda_link: str = Field(description="Funda search link for the supplied address")
