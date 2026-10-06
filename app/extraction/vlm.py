import os
import json
import logging
import time
from typing import List, Dict, Any, Union

from app.core.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_TYPES = ["invoice", "receipt", "bank_statement", "id_card", "form"]

# ✅ FAST model primary, bigger fallback
GROQ_TEXT_MODEL = "openai/gpt-oss-20b"       # fast
GROQ_FALLBACK_MODEL = "openai/gpt-oss-120b"  # slower but smarter fallback

REQUEST_TIMEOUT = 30
MAX_TOKENS = 2048
MAX_PAGES_TO_PROCESS = 1

_ocr_engine = None


def _get_ocr():
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR
        t0 = time.time()
        _ocr_engine = RapidOCR()
        logger.info(f"RapidOCR loaded in {time.time()-t0:.1f}s")
    return _ocr_engine


def _ocr_image(image_path: str) -> str:
    engine = _get_ocr()
    result, _ = engine(image_path)
    if not result:
        return ""
    return "\n".join(line[1] for line in result if line and len(line) > 1)


def _groq_client():
    from groq import Groq
    api_key = getattr(settings, "GROQ_API_KEY", None) or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    return Groq(api_key=api_key, timeout=REQUEST_TIMEOUT)


# ==========================================================
# SHORTER PROMPT (faster) but still asks for spelling fix
# ==========================================================
def _build_prompt(text: str, document_type: str) -> str:
    type_hint = document_type if document_type and document_type != "auto" else "auto-detect"

    return f"""Extract structured data from this {type_hint} document.

OCR text (may have typos):
---
{text[:6000]}
---

Fix obvious OCR typos in addresses/cities (e.g., "Kamataka" → "Karnataka", "Wllage" → "Village").
Do NOT invent data.

Return ONLY JSON:
{{
  "document_type": "invoice|receipt|bank_statement|id_card|form",
  "fields": {{
    "invoice_number": {{"value": "...", "confidence": 0.95}},
    "invoice_date": {{"value": "...", "confidence": 0.95}},
    "order_id": {{"value": "...", "confidence": 0.95}},
    "seller_name": {{"value": "...", "confidence": 0.95}},
    "seller_address": {{"value": "...", "confidence": 0.9}},
    "seller_gstin": {{"value": "...", "confidence": 0.95}},
    "buyer_name": {{"value": "...", "confidence": 0.95}},
    "buyer_address": {{"value": "...", "confidence": 0.9}},
    "subtotal": {{"value": "...", "confidence": 0.95}},
    "tax": {{"value": "...", "confidence": 0.95}},
    "total": {{"value": "...", "confidence": 0.95}},
    "currency": {{"value": "INR", "confidence": 0.95}}
  }},
  "line_items": [
    {{"description": "...", "quantity": 0, "unit_price": 0, "amount": 0}}
  ]
}}

No markdown. Raw JSON only."""


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        if len(parts) >= 2:
            raw = parts[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start >= 0 and end > start:
        raw = raw[start:end + 1]
    return json.loads(raw)


def _call_groq_text(prompt: str) -> str:
    client = _groq_client()
    last_err = None
    for model in [GROQ_TEXT_MODEL, GROQ_FALLBACK_MODEL]:
        try:
            logger.info(f"Trying Groq model: {model}")
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Extract JSON only. Fix OCR typos."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=MAX_TOKENS,
            )
            content = resp.choices[0].message.content or ""
            logger.info(f"Groq {model} OK — {len(content)} chars")
            return content
        except Exception as e:
            last_err = e
            logger.warning(f"Groq {model} failed: {e}")
            continue
    raise RuntimeError(f"All Groq failed: {last_err}")


def _process_single_page(image_path: str, document_type: str, page_num: int,
                          total_pages: int) -> Dict[str, Any]:
    if not os.path.exists(image_path):
        return {"fields": {}, "line_items": [], "_page": page_num}

    t0 = time.time()
    try:
        logger.info(f"Page {page_num}/{total_pages} → OCR")
        text = _ocr_image(image_path)
        t_ocr = time.time() - t0
        logger.info(f"Page {page_num} OCR took {t_ocr:.1f}s, {len(text)} chars")

        if not text.strip():
            return {"fields": {}, "line_items": [], "_page": page_num, "error": "empty OCR"}

        logger.info(f"Page {page_num}/{total_pages} → Groq text")
        prompt = _build_prompt(text, document_type)
        raw = _call_groq_text(prompt)
        t_llm = time.time() - t0 - t_ocr

        parsed = _extract_json(raw)
        parsed["_page"] = page_num

        n_fields = len(parsed.get("fields", {}))
        n_items = len(parsed.get("line_items", []))
        logger.info(f"Page {page_num}/{total_pages} ✓ OCR {t_ocr:.1f}s + LLM {t_llm:.1f}s = {t_ocr+t_llm:.1f}s | {n_fields} fields, {n_items} items")
        return parsed

    except Exception as e:
        import traceback
        t_total = time.time() - t0
        logger.error(f"Page {page_num}/{total_pages} ✗ {t_total:.1f}s: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        return {"fields": {}, "line_items": [], "_page": page_num, "error": str(e)}


def classify_document_type(image_path: str) -> str:
    return "auto"


def extract_with_vlm(image_paths: Union[str, List[str]], document_type: str = "auto") -> Dict[str, Any]:
    if isinstance(image_paths, str):
        image_paths = [image_paths]
    if not image_paths:
        return {"status": "failed", "error": "no pages", "fields": {}, "line_items": []}

    total = len(image_paths)
    pages = image_paths[:MAX_PAGES_TO_PROCESS]
    logger.info(f"VLM: {total} page(s) | processing {len(pages)}")

    _get_ocr()

    t_all = time.time()
    results = [_process_single_page(p, document_type, i + 1, total) for i, p in enumerate(pages)]
    logger.info(f"VLM total: {time.time()-t_all:.1f}s")

    first_result = results[0] if results else None
    if first_result and first_result.get("error"):
        err = first_result.get("error")
        logger.error(f"VLM FAILED: {err}")
        return {"status": "failed", "error": err, "fields": {}, "line_items": [], "page_count": total}

    merged_fields = {}
    merged_items = []
    detected_type = document_type

    for pr in results:
        if not pr:
            continue
        if pr.get("document_type") and detected_type == "auto":
            detected_type = pr["document_type"]
        for k, v in (pr.get("fields") or {}).items():
            if isinstance(v, dict):
                val = v.get("value")
                conf = v.get("confidence", 0.5)
            else:
                val = v
                conf = 0.5
            if val is None or val == "" or str(val).lower() in ("none", "null", "n/a"):
                continue
            if k not in merged_fields or conf > merged_fields[k].get("confidence", 0):
                merged_fields[k] = {"value": val, "confidence": conf}
        for item in (pr.get("line_items") or []):
            if item and not all(v is None for v in item.values()):
                merged_items.append(item)

    logger.info(f"VLM FINAL: {len(merged_fields)} fields, {len(merged_items)} line items")
    return {
        "status": "success",
        "document_type": detected_type,
        "fields": merged_fields,
        "line_items": merged_items,
        "page_count": total,
    }


run_vlm_extraction = extract_with_vlm
extract_document = extract_with_vlm
VLM_MODELS = [GROQ_TEXT_MODEL, GROQ_FALLBACK_MODEL]