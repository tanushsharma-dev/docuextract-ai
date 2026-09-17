from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.document_service import DocumentService
from app.services.storage import save_upload

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/")
def list_documents(db: Session = Depends(get_db)):
    service = DocumentService(db)
    documents = service.list_documents()
    return [{
        "id": document.id,
        "filename": document.filename,
        "status": document.status,
        "confidence": document.confidence,
        "is_valid": document.is_valid,
    } for document in documents]


@router.post("/upload")
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")
    file_bytes = file.file.read()
    saved_path = save_upload(file_bytes, file.filename)
    service = DocumentService(db)
    document = service.create_document(file.filename, file.content_type)
    return {
        "id": document.id,
        "filename": document.filename,
        "storage_path": saved_path,
        "status": document.status,
    }
