from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float


class InvoiceSchema(BaseModel):
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total_amount: Optional[float] = None
    customer_name: Optional[str] = None
    payment_terms: Optional[str] = None
    line_items: List[LineItem] = []

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        if v:
            return v.upper()
        return v


class ReceiptSchema(BaseModel):
    merchant_name: Optional[str] = None
    receipt_date: Optional[str] = None
    total_amount: Optional[float] = None
    tax: Optional[float] = None
    payment_method: Optional[str] = None
    items: List[dict] = []