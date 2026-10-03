import json
import logging
import base64
import io

import PIL.Image
from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None
_groq_client = None

GEMINI_MODELS = ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-2.5-flash"]
GROQ_MODELS = ["qwen/qwen3.8-27b"]

SUPPORTED_TYPES = ["invoice", "receipt", "bank_statement", "id_card", "form"]

SCHEMAS = {
    "invoice": '{"vendor_name":"string or null","invoice_number":"string or null","invoice_date":"YYYY-MM-DD or null","currency":"3-letter code or null","subtotal":"number or null","tax":"number or null","total_amount":"number or null","customer_name":"string or null","line_items":[{"description":"string","quantity":"number","unit_price":"number","amount":"number"}]}',
    "receipt": '{"merchant_name":"string or null","receipt_date":"YYYY-MM-DD or null","total_amount":"number or null","tax":"number or null","payment_method":"string or null","currency":"3-letter code or null","items":[{"description":"string","amount":"number"}]}',
    "bank_statement": '{"bank_name":"string or null","account_holder":"string or null","account_number":"string or null","statement_period":"string or null","opening_balance":"number or null","closing_balance":"number or null","currency":"3-letter code or null","transactions":[{"date":"YYYY-MM-DD","description":"string","amount":"number"}]}',
    "id_card": '{"full_name":"string or null","id_number":"string or null","date_of_birth":"YYYY-MM-DD or null","issue_date":"YYYY-MM-DD or null","expiry_date":"YYYY-MM-DD or null","address":"string or null","document_type":"string or null"}',
    "form": '{"form_title":"string or null","full_name":"string or null","email":"string or null","phone":"string or null","date":"YYYY-MM-DD or null","organization":"string or null"}',
}

RULES = ("You are a precise document extraction engine. Extract structured information from this document. "
         "Rules: 1. Return ONLY valid JSON. 2. If a field is missing, use null. 3. Do NOT invent values. "
         "4. Dates in YYYY-MM-DD. 5. Amounts as numbers without symbols. 6. Currency as 3-letter code if visible. "
         "7. If unsure, prefer null.\nSchema:\n")


def _is_pdf(path):
    try:
        with open(path, "rb") as f:
            return f.read(5) == b"%PDF-"
    except Exception:
        return False


def get_client():
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set in .env!")
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def get_groq_client():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set in .env!")
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client


def build_prompt(document_type):
    return RULES + SCHEMAS.get(document_type, SCHEMAS["invoice"])


def _parse(text):
    content = text.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    return json.loads(content.strip())


def _to_image(file_path):
    if _is_pdf(file_path):
        import fitz
        doc = fitz.open(file_path)
        pix = doc[0].get_pixmap(dpi=150)
        img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img
    return PIL.Image.open(file_path).convert("RGB")


def _call_gemini(file_path, prompt):
    client = get_client()
    config = types.GenerateContentConfig(temperature=0.1, response_mime_type="application/json")
    last_error = None

    models = [settings.VLM_MODEL] + [m for m in GEMINI_MODELS if m != settings.VLM_MODEL]

    for model in models:
        try:
            if _is_pdf(file_path):
                with open(file_path, "rb") as f:
                    data = f.read()
                contents = [prompt, types.Part.from_bytes(data=data, mime_type="application/pdf")]
            else:
                contents = [prompt, PIL.Image.open(file_path).convert("RGB")]

            resp = client.models.generate_content(model=model, contents=contents, config=config)
            logger.info(f"Gemini OK with model: {model}")
            return _parse(resp.text)
        except Exception as e:
            last_error = e
            logger.warning(f"Gemini model {model} failed: {e}")

    raise last_error


def _call_groq(file_path, prompt):
    client = get_groq_client()
    img = _to_image(file_path)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    last_error = None

    for model in GROQ_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ]}],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            logger.info(f"Groq OK with model: {model}")
            return _parse(response.choices[0].message.content)
        except Exception as e:
            last_error = e
            logger.warning(f"Groq model {model} failed: {e}")

    raise last_error


def extract_with_vlm(file_path, document_type="invoice"):
    prompt = build_prompt(document_type)
    errors = []

    if settings.VLM_PROVIDER.lower() == "groq":
        order = [_call_groq, _call_gemini]
    else:
        order = [_call_gemini, _call_groq]

    for fn in order:
        try:
            return fn(file_path, prompt)
        except Exception as e:
            errors.append(f"{fn.__name__}: {e}")

    return {"error": " | ".join(errors)}


def classify_document_type(ocr_text):
    t = ocr_text.lower()
    if any(k in t for k in ["bank statement", "account statement", "statement of account"]):
        return "bank_statement"
    if any(k in t for k in ["passport", "driving license", "identity card", "aadhaar", "id card"]):
        return "id_card"
    if any(k in t for k in ["receipt", "cash memo", "payment receipt"]):
        return "receipt"
    return "invoice"