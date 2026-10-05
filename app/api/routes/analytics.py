import time

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Document, ExtractedField

router = APIRouter()

_cache = {"data": None, "ts": 0}
TTL = 60


@router.get("/overview")
def analytics_overview(db: Session = Depends(get_db)):
    now = time.time()
    if _cache["data"] and (now - _cache["ts"]) < TTL:
        return {**_cache["data"], "cached": True}

    total = db.query(func.count(Document.id)).scalar() or 0
    by_status = dict(db.query(Document.status, func.count(Document.id)).group_by(Document.status).all())
    by_type = dict(db.query(Document.document_type, func.count(Document.id)).group_by(Document.document_type).all())
    avg_conf = db.query(func.avg(ExtractedField.confidence)).scalar() or 0

    data = {
        "total_documents": total,
        "needs_review": by_status.get("needs_review", 0),
        "auto_approved": by_status.get("extracted", 0),
        "failed": by_status.get("failed", 0),
        "by_type": by_type,
        "avg_confidence": round(float(avg_conf) * 100, 1),
    }
    _cache["data"] = data
    _cache["ts"] = now
    return data