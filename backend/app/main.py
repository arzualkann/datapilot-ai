from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.query import router as query_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3001"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

app.include_router(query_router, prefix="/api")


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Return a lightweight status response for local checks."""
    return {"status": "ok", "service": "datapilot-ai-api"}
