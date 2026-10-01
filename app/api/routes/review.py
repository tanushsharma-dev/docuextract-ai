from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from typing import Dict, Optional
from app.core.database import get_db
from app.models import Document, HumanReview, ExtractedField

router = APIRouter()


class ReviewSubmission(BaseModel):
    corrections: Dict[str, str]
    review_status: str = "approved"
    reviewer_name: str = "anonymous"
    comments: Optional[str] = None


@router.get("/pending")
def get_pending_reviews(db: Session = Depends(get_db)):
    docs = db.query(Document).filter(Document.status == "needs_review").all()
    return [{"document_id": str(d.id), "filename": d.filename} for d in docs]


@router.get("/{document_id}")
def get_review_data(document_id: UUID, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    fields = db.query(ExtractedField).filter(
        ExtractedField.document_id == document_id
    ).all()

    return {
        "document_id": str(doc.id),
        "filename": doc.filename,
        "storage_path": doc.storage_path,
        "fields": [
            {
                "field_name": f.field_name,
                "value": f.normalized_value,
                "confidence": f.confidence,
                "requires_review": f.requires_review
            }
            for f in fields
        ]
    }


@router.post("/{document_id}")
def submit_review(document_id: UUID, data: ReviewSubmission, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    for field_name, corrected_value in data.corrections.items():
        field = db.query(ExtractedField).filter(
            ExtractedField.document_id == document_id,
            ExtractedField.field_name == field_name
        ).first()

        original = field.normalized_value if field else None

        review = HumanReview(
            document_id=document_id,
            field_name=field_name,
            original_value=original,
            corrected_value=corrected_value,
            reviewer_name=data.reviewer_name,
            review_status=data.review_status,
            comments=data.comments
        )
        db.add(review)

        if field:
            field.normalized_value = corrected_value
            field.requires_review = False
            field.confidence = 1.0
            field.source = "human"

    doc.status = "reviewed"
    db.commit()

    return {"status": "success", "message": "Review saved"}