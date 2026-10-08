import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Document, ExtractedField, LineItem, User
from app.api.routes.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# ==========================================================
# MAIN ENDPOINT — /api/v1/analytics/overview
# (Frontend ye call karta hai — user-isolated data)
# ==========================================================
@router.get("/overview")
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Overview stats — ONLY current user's documents."""
    uid = current_user.id

    total = db.query(func.count(Document.id)).filter(Document.user_id == uid).scalar() or 0

    auto_approved = db.query(func.count(Document.id)).filter(
        Document.user_id == uid,
        Document.status == "extracted",
    ).scalar() or 0

    needs_review = db.query(func.count(Document.id)).filter(
        Document.user_id == uid,
        Document.status == "needs_review",
    ).scalar() or 0

    failed = db.query(func.count(Document.id)).filter(
        Document.user_id == uid,
        Document.status == "failed",
    ).scalar() or 0

    processing = db.query(func.count(Document.id)).filter(
        Document.user_id == uid,
        Document.status.in_(["uploaded", "processing"]),
    ).scalar() or 0

    # Document types distribution
    type_rows = (
        db.query(Document.document_type, func.count(Document.id))
        .filter(Document.user_id == uid)
        .group_by(Document.document_type)
        .all()
    )
    doc_types = [{"type": t or "unknown", "count": c} for t, c in type_rows]

    # Average confidence (join with user filter)
    avg_conf = db.query(func.avg(ExtractedField.confidence)).join(
        Document, Document.id == ExtractedField.document_id
    ).filter(Document.user_id == uid).scalar()
    avg_confidence = round(float(avg_conf) * 100) if avg_conf is not None else 0

    # Total fields and line items
    total_fields = db.query(func.count(ExtractedField.id)).join(
        Document, Document.id == ExtractedField.document_id
    ).filter(Document.user_id == uid).scalar() or 0

    total_line_items = db.query(func.count(LineItem.id)).join(
        Document, Document.id == LineItem.document_id
    ).filter(Document.user_id == uid).scalar() or 0

    # Multiple key naming conventions for frontend compatibility
    return {
        # Primary names
        "total_documents": total,
        "auto_approved": auto_approved,
        "needs_review": needs_review,
        "failed": failed,
        "processing": processing,
        "avg_confidence": avg_confidence,

        # Alias names (frontend variations)
        "total": total,
        "extracted": auto_approved,
        "accuracy": avg_confidence,
        "document_types": doc_types,

        # Extra info
        "total_fields": total_fields,
        "total_line_items": total_line_items,
    }


# ==========================================================
# SUMMARY (alternative endpoint)
# ==========================================================
@router.get("/summary")
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Alias for /overview — same data."""
    return get_overview(db, current_user)


# ==========================================================
# TRENDS — daily uploads
# ==========================================================
@router.get("/trends")
def get_analytics_trends(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Daily upload counts for last N days — user only."""
    uid = current_user.id
    since = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.query(
            func.date(Document.created_at).label("day"),
            func.count(Document.id).label("count"),
        )
        .filter(Document.user_id == uid, Document.created_at >= since)
        .group_by(func.date(Document.created_at))
        .order_by(func.date(Document.created_at))
        .all()
    )

    return {
        "days": days,
        "data": [{"date": str(d), "count": c} for d, c in rows],
    }


# ==========================================================
# RECENT ACTIVITY
# ==========================================================
@router.get("/recent")
def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recent documents — user only."""
    uid = current_user.id

    docs = (
        db.query(Document)
        .filter(Document.user_id == uid)
        .order_by(desc(Document.created_at))
        .limit(limit)
        .all()
    )

    return {
        "documents": [
            {
                "document_id": str(d.id),
                "filename": d.filename,
                "status": d.status,
                "document_type": d.document_type,
                "created_at": str(d.created_at),
            }
            for d in docs
        ]
    }