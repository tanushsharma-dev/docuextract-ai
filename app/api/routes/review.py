from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/review", tags=["review"])


@router.post("/")
def submit_review(document_id: int, approved: bool, notes: str | None = None):
    if document_id <= 0:
        raise HTTPException(status_code=400, detail="document_id must be positive")
    return {
        "document_id": document_id,
        "approved": approved,
        "notes": notes,
        "status": "submitted",
    }
