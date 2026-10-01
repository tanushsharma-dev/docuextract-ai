from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.models import Document, ExtractedField, LineItem
from app.services.storage import save_uploaded_file
from app.services.queue import enqueue_extraction_job

router = APIRouter()


@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("auto"),
    db: Session = Depends(get_db)
):
    allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp", "image/tiff"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Invalid file type: {file.content_type}")

    storage_path = await save_uploaded_file(file)

    doc = Document(
        filename=file.filename,
        mime_type=file.content_type,
        storage_path=storage_path,
        status="uploaded"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    enqueue_extraction_job(str(doc.id), document_type)

    return {
        "document_id": str(doc.id),
        "status": "uploaded",
        "message": "Document received. Processing started."
    }


@router.get("/{document_id}")
def get_document(document_id: UUID, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "document_id": str(doc.id),
        "filename": doc.filename,
        "status": doc.status,
        "document_type": doc.document_type,
        "page_count": doc.page_count
    }


@router.get("/{document_id}/extraction")
def get_extraction(document_id: UUID, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    fields = db.query(ExtractedField).filter(ExtractedField.document_id == document_id).all()
    line_items = db.query(LineItem).filter(LineItem.document_id == document_id).all()

    return {
        "document_id": str(doc.id),
        "document_type": doc.document_type,
        "status": doc.status,
        "fields": {
            f.field_name: {
                "value": f.normalized_value,
                "confidence": f.confidence,
                "requires_review": f.requires_review,
                "source": f.source
            }
            for f in fields
        },
        "line_items": [
            {
                "description": li.description,
                "quantity": li.quantity,
                "unit_price": li.unit_price,
                "amount": li.amount
            }
            for li in line_items
        ]
    }


@router.get("/")
def list_documents(status: str = None, db: Session = Depends(get_db)):
    query = db.query(Document)
    if status:
        query = query.filter(Document.status == status)
    docs = query.order_by(Document.created_at.desc()).limit(50).all()
    return [
        {
            "document_id": str(d.id),
            "filename": d.filename,
            "status": d.status,
            "document_type": d.document_type,
            "created_at": d.created_at.isoformat()
        }
        for d in docs
    ]