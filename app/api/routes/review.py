from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.models import Document
from app.services.storage import save_uploaded_file
from app.services.queue import enqueue_extraction_job

router = APIRouter()

@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate file type
    allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp", "image/tiff"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Invalid file type: {file.content_type}")

    # Save file
    storage_path = await save_uploaded_file(file)

    # Create document record
    doc = Document(
        filename=file.filename,
        mime_type=file.content_type,
        storage_path=storage_path,
        status="uploaded"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Queue extraction job
    enqueue_extraction_job(str(doc.id))

    return {
        "document_id": str(doc.id),
        "status": "uploaded",
        "message": "Document received. Processing queued."
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