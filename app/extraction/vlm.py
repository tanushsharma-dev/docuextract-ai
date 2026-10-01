import json
import logging

import PIL.Image
from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None

SUPPORTED_TYPES = ["invoice", "receipt", "bank_statement", "id_card", "form"]

SCHEMAS = {
    "invoice": """
{
  "vendor_name": "string or null",
  "invoice_number": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "currency": "3-letter code or null",
  "subtotal": "number or null",
  "tax": "number or null",
  "total_amount": "number or null",
  "customer_name": "string or null",
  "line_items": [{"description": "string", "quantity": "number", "unit_price": "number", "amount": "number"}]
}
""",
    "receipt": """
{
  "merchant_name": "string or null",
  "receipt_date": "YYYY-MM-DD or null",
  "total_amount": "number or null",
  "tax": "number or null",
  "payment_method": "string or null",
  "currency": "3-letter code or null",
  "items": [{"description": "string", "amount": "number"}]
}
""",
    "bank_statement": """
{
  "bank_name": "string or null",
  "account_holder": "string or null",
  "account_number": "string or null",
  "statement_period": "string or null",
  "opening_balance": "number or null",
  "closing_balance": "number or null",
  "currency": "3-letter code or null",
  "transactions": [{"date": "YYYY-MM-DD", "description": "string", "amount": "number"}]
}
""",
    "id_card": """
{
  "full_name": "string or null",
  "id_number": "string or null",
  "date_of_birth": "YYYY-MM-DD or null",
  "issue_date": "YYYY-MM-DD or null",
  "expiry_date": "YYYY-MM-DD or null",
  "address": "string or null",
  "document_type": "string or null"
}
""",
    "form": """
{
  "form_title": "string or null",
  "full_name": "string or null",
  "email": "string or null",
  "phone": "string or null",
  "date": "YYYY-MM-DD or null",
  "organization": "string or null"
}
"""
}

RULES = """You are a precise document extraction engine.

Extract structured information from this document image.

Rules:
1. Return ONLY valid JSON. No markdown, no explanations.
2. If a field is missing, use null.
3. Do NOT invent values.
4. Dates must be in YYYY-MM-DD format.
5. Amounts must be numbers without currency symbols.
6. Currency must be a 3-letter code if visible.
7. If unsure, prefer null over guessing.
"""


def get_client():
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set in .env file!")
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info(f"Gemini client ready (model: {settings.VLM_MODEL})")
    return _client


def build_prompt(document_type: str) -> str:
    schema = SCHEMAS.get(document_type, SCHEMAS["invoice"])
    return RULES + "\nSchema:\n" + schema


def extract_with_vlm(image_path: str, document_type: str = "invoice") -> dict:
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
    text_lower = ocr_text.lower()
    if any(k in text_lower for k in ["bank statement", "account statement", "statement of account"]):
        return "bank_statement"
    if any(k in text_lower for k in ["passport", "driving license", "identity card", "aadhaar", "id card"]):
        return "id_card"
    if any(k in text_lower for k in ["receipt", "cash memo", "payment receipt"]):
        return "receipt"
    return "invoice"