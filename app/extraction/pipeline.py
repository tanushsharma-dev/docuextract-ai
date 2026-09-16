from __future__ import annotations

from app.extraction.confidence import compute_confidence
from app.extraction.layout import detect_layout
from app.extraction.ocr import run_ocr
from app.extraction.preprocessing import preprocess_bytes
from app.extraction.rules import validate_amount
from app.extraction.validation import validate_extraction
from app.extraction.vlm import extract_structured_data


def run_document_pipeline(file_path: str, file_bytes: bytes) -> dict:
    cleaned = preprocess_bytes(file_bytes)
    ocr_text = run_ocr(file_path)
    layout = detect_layout(ocr_text)
    structured_data = extract_structured_data(ocr_text)
    amount_result = validate_amount(float(structured_data.get("amount", 0.0)))
    validation = validate_extraction(structured_data)
    confidence = compute_confidence(layout["quality_score"], 0.8 if amount_result.passed else 0.3)
    return {
        "file_path": file_path,
        "bytes_processed": len(cleaned),
        "layout": layout,
        "structured_data": structured_data,
        "validation": validation,
        "confidence": confidence,
    }
