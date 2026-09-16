from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentDocument(BaseModel):
    id: int | None = None
    filename: str
    content_type: str | None = None
    status: str = "uploaded"


class ValidationIssue(BaseModel):
    field: str
    message: str
    severity: str = Field(default="warning")
