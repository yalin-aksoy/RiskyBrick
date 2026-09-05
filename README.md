# RiskyBrick API

A scalable Python 3.11+ backend foundation using FastAPI.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

## Run locally

```bash
uvicorn app.main:app --reload
```

The API is available at http://127.0.0.1:8000. Interactive documentation is available at `/docs`.

The BAG property endpoint is available at `/api/bag/property`. It queries the
official PDOK Locatieserver, which is backed by BAG, and returns the BAG
addressable-object ID, address-designation ID, normalized address details, and
the corresponding Funda search link:

```text
GET /api/bag/property?address=Damrak%201&postcode=1012%20LG
```

The endpoint is intended for live address validation. For bulk historical or
local analysis, use a BAG information product or download instead; those
products can differ in included objects, attributes, and relationships.

Foundation indicators are available at `/api/foundation-stability`. The first
regional provider is `zaanstad`; it queries Zaanstad map layers for historical
filled or raised areas and soil activity indicators. The response uses
`indicators_found` or `not_enough_foundation_info` and never presents these
indicators as a structural safety assessment. Additional regions can be added
as providers without changing the endpoint contract.

For Zaanstad, the provider also queries the foundation reference-card layer
`geo:zamo_pand_verrijkt`. When a card matches the BAG address, its details can
include foundation status, classification, construction year, investigation
year, restoration year, monitoring status, and conclusion.

Use `/api/risk-info` when you want the combined response containing BAG
identity, the Funda link, and regional foundation-risk indicators.

## Test and lint

```bash
pytest
ruff check .
```

## Structure

- `app/main.py`: FastAPI application entry point
- `app/api/`: versionable route registration and endpoints
- `app/core/`: shared configuration and infrastructure
- `tests/`: focused API tests
- `.github/agents/fastapi-backend.agent.md`: workspace custom agent for backend work
