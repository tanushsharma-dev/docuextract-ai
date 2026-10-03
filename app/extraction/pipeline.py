import logging
from typing import Dict
from app.extraction.preprocessing import preprocess_document
from app.extraction.ocr import run_ocr
from app.extraction.vlm import extract_with_vlm, classify_document_type, SUPPORTED_TYPES
from app.extraction.rules import rule_based_extraction
from app.extraction.validation import validate_extracted_data
from app.extraction.confidence import calculate_field_confidence, requires_review

logger = logging.getLogger(__name__)


def run_extraction_pipeline(file_path: str, output_dir: str, doc_type_hint: str = "auto") -> Dict:
    result = {"status": "success", "document_type": None, "fields": {}, "line_items": [], "validation": {}, "requires_review": False}

    try:
        logger.info("Step 1: Preprocessing")
        image_paths = preprocess_document(file_path, output_dir)

        logger.info("Step 2: OCR")
        ocr_text = run_ocr(image_paths[0] if image_paths else file_path)["full_text"]

        logger.info("Step 3: Document type")
        doc_type = doc_type_hint if (doc_type_hint != "auto" and doc_type_hint in SUPPORTED_TYPES) else classify_document_type(ocr_text)
        result["document_type"] = doc_type

        logger.info("Step 4: VLM extraction")
        vlm_output = extract_with_vlm(file_path, doc_type)
        if "error" in vlm_output:
            logger.error(f"VLM failed: {vlm_output['error']}")
            result["status"] = "failed"
            result["error"] = vlm_output["error"]
            result["page_count"] = 1
            return result
        logger.info("Step 5: Rules")
        rule_output = rule_based_extraction(ocr_text, doc_type)

        logger.info("Step 6: Merge + confidence")
        merged = {}
        for field in set(list(vlm_output.keys()) + list(rule_output.keys())):
            if field in ("line_items", "items", "transactions"):
                continue
            vlm_val = vlm_output.get(field)
            rule_val = rule_output.get(field)
            conf = calculate_field_confidence(field_name=field, ocr_value=None, vlm_value=vlm_val, rule_value=rule_val, validation_passed=True)
            merged[field] = {
                "value": vlm_val if vlm_val is not None else rule_val,
                "confidence": round(conf, 3),
                "requires_review": requires_review(conf),
                "source": "vlm" if vlm_val is not None else "rule",
            }
            if requires_review(conf):
                result["requires_review"] = True

        result["fields"] = merged
        result["line_items"] = vlm_output.get("line_items") or vlm_output.get("items") or vlm_output.get("transactions") or []

        logger.info("Step 7: Validation")
        flat = {k: v["value"] for k, v in merged.items()}
        flat["line_items"] = result["line_items"]
        result["validation"] = validate_extracted_data(flat, doc_type)
        if not result["validation"]["valid"]:
            result["requires_review"] = True

        result["page_count"] = len(image_paths) if image_paths else 1

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        result["status"] = "failed"
        result["error"] = str(e)

    return result