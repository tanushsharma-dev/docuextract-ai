import json
import logging

import PIL.Image
from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None


def get_client():
    """Initialize Gemini client once (singleton)."""
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set in .env file!")
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info(f"Gemini client ready (model: {settings.VLM_MODEL})")
    return _client


INVOICE_SCHEMA = """
{
  "vendor_name": "string or null",
  "invoice_number": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "currency": "3-letter code or null",
  "subtotal": "number or null",
  "tax": "number or null",
  "total_amount": "number or null",
  "customer_name": "string or null",
  "payment_terms": "string or null",
  "line_items": [
    {
      "description": "string",
      "quantity": "number",
      "unit_price": "number",
      "amount": "number"
    }
  ]
}
"""

RECEIPT_SCHEMA = """
{
  "merchant_name": "string or null",
  "receipt_date": "YYYY-MM-DD or null",
  "total_amount": "number or null",
  "tax": "number or null",
  "payment_method": "string or null",
  "items": [
    {"description": "string", "amount": "number"}
  ]
}
"""


def build_prompt(document_type: str) -> str:
    schema = INVOICE_SCHEMA if document_type == "invoice" else RECEIPT_SCHEMA
    return f"""You are a precise document extraction engine.

Extract structured information from this document image.

Rules:
1. Return ONLY valid JSON. No markdown, no explanations.
2. If a field is missing, use null.
3. Do NOT invent values.
4. Dates must be in YYYY-MM-DD format.
5. Amounts must be numbers without currency symbols.
6. Currency must be a 3-letter code if visible.
7. If unsure, prefer null over guessing.

Schema:
{schema}
"""


def extract_with_vlm(image_path: str, document_type: str = "invoice") -> dict:
    """Extract structured data using Gemini Vision (FREE)."""
    try:
        client = get_client()
        image = PIL.Image.open(image_path).convert("RGB")
        prompt = build_prompt(document_type)

        response = client.models.generate_content(
            model=settings.VLM_MODEL,
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        content = response.text.strip()

        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        return json.loads(content)

    except Exception as e:
        logger.error(f"Gemini extraction failed: {e}")
        return {"error": str(e)}


def classify_document_type(ocr_text: str) -> str:
    """Classify document type based on OCR text."""
    text_lower = ocr_text.lower()

    if any(kw in text_lower for kw in [
        "tax invoice", "invoice no", "invoice number", "bill no", "inv no"
    ]):
        return "invoice"
    if any(kw in text_lower for kw in [
        "receipt", "cash memo", "payment receipt"
    ]):
        return "receipt"
    return "invoice"