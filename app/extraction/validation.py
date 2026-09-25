from typing import Dict, List, Tuple
import re
from datetime import datetime

def validate_invoice(data: dict) -> Dict:
    """Validate invoice data and return issues."""
    issues = []
    warnings = []

    # Required fields
    required = ["vendor_name", "invoice_number", "total_amount"]
    for field in required:
        if not data.get(field):
            issues.append(f"Missing required field: {field}")

    # Date validation
    for date_field in ["invoice_date", "due_date"]:
        if data.get(date_field):
            try:
                datetime.strptime(data[date_field], "%Y-%m-%d")
            except ValueError:
                issues.append(f"Invalid date format: {date_field}")

    # Currency validation
    if data.get("currency"):
        if not re.match(r"^[A-Z]{3}$", data["currency"]):
            warnings.append(f"Invalid currency code: {data['currency']}")

    # Amount validation
    for amt_field in ["subtotal", "tax", "total_amount"]:
        if data.get(amt_field) is not None and data[amt_field] < 0:
            issues.append(f"Negative amount: {amt_field}")

    # Arithmetic: subtotal + tax ≈ total
    subtotal = data.get("subtotal")
    tax = data.get("tax", 0) or 0
    total = data.get("total_amount")

    if subtotal is not None and total is not None:
        expected = subtotal + tax
        if abs(expected - total) > 1.0:
            issues.append(f"Arithmetic mismatch: subtotal({subtotal}) + tax({tax}) = {expected}, but total = {total}")

    # Line item arithmetic
    line_items = data.get("line_items", [])
    for i, item in enumerate(line_items):
        expected_amount = item.get("quantity", 0) * item.get("unit_price", 0)
        actual_amount = item.get("amount", 0)
        if abs(expected_amount - actual_amount) > 0.5:
            warnings.append(f"Line item {i+1} amount mismatch: {expected_amount} vs {actual_amount}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings
    }

def validate_receipt(data: dict) -> Dict:
    issues = []
    if not data.get("merchant_name"):
        issues.append("Missing merchant_name")
    if not data.get("total_amount"):
        issues.append("Missing total_amount")
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": []
    }

def validate_extracted_data(data: dict, document_type: str) -> Dict:
    if document_type == "invoice":
        return validate_invoice(data)
    elif document_type == "receipt":
        return validate_receipt(data)
    return {"valid": True, "issues": [], "warnings": []}