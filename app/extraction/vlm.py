from __future__ import annotations


def extract_structured_data(document_text: str) -> dict:
    return {
        "vendor": "unknown",
        "amount": 0.0,
        "currency": "USD",
        "raw_text": document_text,
    }
