import base64
import json
import logging
from pathlib import Path
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

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

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def extract_with_vlm(image_path: str, document_type: str = "invoice") -> dict:
    """Extract structured data using Vision-Language Model."""
    schema = INVOICE_SCHEMA if document_type == "invoice" else RECEIPT_SCHEMA

    prompt = f"""You are a precise document extraction engine.

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

    try:
        base64_image = encode_image(image_path)

        response = client.chat.completions.create(
            model=settings.VLM_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.1
        )

        content = response.choices[0].message.content.strip()

        # Clean markdown if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        return json.loads(content)

    except Exception as e:
        logger.error(f"VLM extraction failed: {e}")
        return {"error": str(e)}

def classify_document_type(ocr_text: str) -> str:
    """Classify document type based on OCR text."""
    text_lower = ocr_text.lower()

    if any(kw in text_lower for kw in ["tax invoice", "invoice no", "invoice number", "bill no"]):
        return "invoice"
    if any(kw in text_lower for kw in ["receipt", "cash memo", "bill", "payment receipt"]):
        return "receipt"
    return "unknown"