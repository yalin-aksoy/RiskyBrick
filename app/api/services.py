from urllib.parse import urlencode

FUNDA_SEARCH_URL = "https://www.funda.nl/zoeken/koop/"


def build_funda_link(address: str, postcode: str) -> str:
    query = urlencode({"q": f"{address}, {postcode}"})
    return f"{FUNDA_SEARCH_URL}?{query}"
