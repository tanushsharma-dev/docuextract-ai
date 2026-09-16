from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.documents import router as documents_router
from app.api.routes.evaluation import router as evaluation_router
from app.api.routes.review import router as review_router
from app.core.config import settings

app = FastAPI(
    title="DocuExtract AI",
    description="Document extraction, validation, and review platform",
    version="0.1.0",
    debug=settings.debug,
)

app.include_router(documents_router, prefix="/api/v1")
app.include_router(review_router, prefix="/api/v1")
app.include_router(evaluation_router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "environment": settings.app_env}
