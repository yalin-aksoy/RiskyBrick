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

The API is available at http://127.0.0.1:8000. Interactive documentation is available at `/docs`, and the health endpoint is `/api/health`.

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
