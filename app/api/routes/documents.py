import os
import shutil
import logging
from uuid import UUID, uuid4

import jwt as pyjwt
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import Document, ExtractedField, LineItem, User
from app.api.routes.auth import get_current_user, ALGORITHM
from app.services.queue import enqueue_extraction_job

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_TYPES = [
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/tiff",
]


# ==========================================================
# STATS
# ==========================================================
@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid = current_user.id

    total = db.query(func.count(Document.id)).filter(Document.user_id == uid).scalar() or 0
    extracted = db.query(func.count(Document.id)).filter(
        Document.user_id == uid,
        Document.status.in_(["extracted", "needs_review"]),
    ).scalar() or 0
    failed = db.query(func.count(Document.id)).filter(
        Document.user_id == uid,
        Document.status == "failed",
    ).scalar() or 0
    needs_review = db.query(func.count(Document.id)).filter(
        Document.user_id == uid,
        Document.status == "needs_review",
    ).scalar() or 0
    processing = db.query(func.count(Document.id)).filter(
        Document.user_id == uid,
        Document.status.in_(["uploaded", "processing"]),
    ).scalar() or 0

    avg_conf = db.query(func.avg(ExtractedField.confidence)).join(
        Document, Document.id == ExtractedField.document_id
    ).filter(Document.user_id == uid).scalar()

    accuracy = round(float(avg_conf) * 100) if avg_conf is not None else 0

    return {
        "total": total,
        "extracted": extracted,
        "failed": failed,
        "needs_review": needs_review,
        "processing": processing,
        "accuracy": accuracy,
    }


# ==========================================================
# UPLOAD
# ==========================================================
@router.post("/")
def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("auto"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid file type: {file.content_type}")

    upload_dir = os.path.join(settings.STORAGE_PATH, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    storage_path = os.path.join(upload_dir, f"{uuid4()}_{file.filename}")

    with open(storage_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    doc = Document(
        filename=file.filename,
        mime_type=file.content_type,
        storage_path=storage_path,
        status="uploaded",
        user_id=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    enqueue_extraction_job(str(doc.id), document_type)

    return {
        "document_id": str(doc.id),
        "status": "uploaded",
        "message": "Document received. Processing started.",
    }


# ==========================================================
# LIST
# ==========================================================
@router.get("/")
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    docs = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .limit(50)
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


# ==========================================================
# DOWNLOAD ORIGINAL FILE
# NOTE: Must come before /{document_id} route
# ==========================================================
@router.get("/{document_id}/download")
def download_document(
    document_id: UUID,
    token: str = None,
    db: Session = Depends(get_db),
):
    """Download original file. Auth via query param token."""
    if not token:
        raise HTTPException(401, "Token required")

    try:
        payload = pyjwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
    except Exception:
        raise HTTPException(401, "Invalid or expired token")

    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == user_id)
        .first()
    )
    if not doc:
        raise HTTPException(404, "Document not found")

    if not os.path.exists(doc.storage_path):
        raise HTTPException(404, "File not found on disk")

    return FileResponse(
        path=doc.storage_path,
        filename=doc.filename,
        media_type=doc.mime_type or "application/octet-stream",
    )


# ==========================================================
# SINGLE DOCUMENT
# ==========================================================
@router.get("/{document_id}")
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "document_id": str(doc.id),
        "filename": doc.filename,
        "status": doc.status,
        "document_type": doc.document_type,
        "page_count": doc.page_count,
        "created_at": str(doc.created_at),
    }


# ==========================================================
# EXTRACTION RESULT
# ==========================================================
@router.get("/{document_id}/extraction")
def get_extraction(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    fields = db.query(ExtractedField).filter(ExtractedField.document_id == doc.id).all()
    items = db.query(LineItem).filter(LineItem.document_id == doc.id).all()

    return {
        "document_id": str(doc.id),
        "status": doc.status,
        "document_type": doc.document_type,
        "fields": {
            f.field_name: {
                "value": f.normalized_value,
                "confidence": f.confidence,
                "source": f.source,
                "requires_review": f.requires_review,
            }
            for f in fields
        },
        "line_items": [
            {
                "description": i.description,
                "quantity": i.quantity,
                "unit_price": i.unit_price,
                "amount": i.amount,
            }
            for i in items
        ],
    }