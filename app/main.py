from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="0.1.0",
)

app.include_router(api_router, prefix="/api")


@app.get("/", tags=["system"])
def read_root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "ok"}
