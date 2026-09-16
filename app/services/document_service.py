from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentService:
    def __init__(self, db: Session):
        self.db = db

    def create_document(self, filename: str, content_type: str | None = None) -> Document:
        document = Document(filename=filename, content_type=content_type, status="uploaded")
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def update_status(self, document_id: int, status: str, confidence: float | None = None, is_valid: bool | None = None) -> Document | None:
        document = self.db.get(Document, document_id)
        if document is None:
            return None
        document.status = status
        if confidence is not None:
            document.confidence = confidence
        if is_valid is not None:
            document.is_valid = is_valid
        self.db.commit()
        self.db.refresh(document)
        return document

    def list_documents(self) -> list[Document]:
        return self.db.query(Document).order_by(Document.created_at.desc()).all()

    def get_document(self, document_id: int) -> Document | None:
        return self.db.get(Document, document_id)
