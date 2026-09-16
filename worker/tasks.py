from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery("docuextract", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task(name="process_document")
def process_document(document_id: int) -> dict:
    return {"document_id": document_id, "status": "processed"}
