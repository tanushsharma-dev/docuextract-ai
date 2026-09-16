from __future__ import annotations


def detect_layout(document_text: str) -> dict:
    return {
        "paragraphs": len(document_text.splitlines()),
        "tables_detected": 0,
        "quality_score": 0.9,
    }
