import os
import shutil
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import Document, ExtractedField, LineItem, User
from app.api.routes.auth import get_current_user
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


@router.post("/")
def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("auto"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload endpoint — sync mode me process hota hai."""
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


@router.get("/")
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List ONLY current user's documents."""
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