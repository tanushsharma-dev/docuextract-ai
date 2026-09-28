from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db          # agar tumhare project me path alag ho (jaise app.database) to wahi use karo
from app.models import Document, ExtractedField, LineItem

router = APIRouter(tags=["extraction"])


@router.get("/{document_id}/extraction")
def get_extraction(document_id: UUID, db: Session = Depends(get_db)):
    # 1. Document dhundo
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 2. Extracted fields
    fields = (
        db.query(ExtractedField)
        .filter(ExtractedField.document_id == document_id)
        .all()
    )

    # 3. Line items
    line_items = (
        db.query(LineItem)
        .filter(LineItem.document_id == document_id)
        .all()
    )

    # 4. Response build karo
    return {
        "document_id": str(doc.id),
        "document_type": doc.document_type,
        "status": doc.status,
        "fields": {
            f.field_name: {
                "value": f.normalized_value,
                "confidence": f.confidence,
                "requires_review": f.requires_review,
                "source": f.source,
            }
            for f in fields
        },
        "line_items": [
            {
                "description": li.description,
                "quantity": li.quantity,
                "unit_price": li.unit_price,
                "amount": li.amount,
            }
            for li in line_items
        ],
    }