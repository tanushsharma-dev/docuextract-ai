from __future__ import annotations

from pydantic import BaseModel, Field


class InvoiceExtraction(BaseModel):
    vendor_name: str | None = None
    invoice_number: str | None = None
    issue_date: str | None = None
    due_date: str | None = None
    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    currency: str = "USD"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
