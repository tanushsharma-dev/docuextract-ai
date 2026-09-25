import re
from typing import Dict, Optional

def extract_invoice_number(text: str) -> Optional[str]:
    patterns = [
        r"Invoice\s*(?:No|Number|#|ID)?\s*[:\-]?\s*([A-Z0-9\-/]+)",
        r"Inv\s*(?:No|Number)?\s*[:\-]?\s*([A-Z0-9\-/]+)",
        r"Bill\s*(?:No|Number)?\s*[:\-]?\s*([A-Z0-9\-/]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def extract_date(text: str) -> Optional[str]:
    patterns = [
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
        r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            try:
                if len(groups[0]) == 4:
                    return f"{groups[0]}-{int(groups[1]):02d}-{int(groups[2]):02d}"
                else:
                    return f"{groups[2]}-{int(groups[1]):02d}-{int(groups[0]):02d}"
            except:
                pass
    return None

def extract_total_amount(text: str) -> Optional[float]:
    patterns = [
        r"(?:Total|Grand\s*Total|Amount\s*Due)\s*[:\-]?\s*Rs?\.?\s*([\d,]+\.?\d*)",
        r"(?:Total|Grand\s*Total)\s*[:\-]?\s*([\d,]+\.?\d*)",
        r"([\d,]+\.\d{2})\s*$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(",", "")
            try:
                return float(amount_str)
            except:
                pass
    return None

def rule_based_extraction(ocr_text: str, document_type: str) -> Dict:
    """Extract fields using regex rules."""
    if document_type == "invoice":
        return {
            "invoice_number": extract_invoice_number(ocr_text),
            "invoice_date": extract_date(ocr_text),
            "total_amount": extract_total_amount(ocr_text),
        }
    return {}