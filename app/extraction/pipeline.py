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
    result = {
        "status": "success",
        "document_type": None,
        "fields": {},
        "line_items": [],
        "validation": {},
        "requires_review": False
    }

    try:
        logger.info("Step 1: Preprocessing document")
        image_paths = preprocess_document(file_path, output_dir)
        if not image_paths:
            raise ValueError("No images generated from document")

        primary_image = image_paths[0]

        logger.info("Step 2: Running OCR")
        ocr_result = run_ocr(primary_image)
        ocr_text = ocr_result["full_text"]

        logger.info("Step 3: Document type")
        if doc_type_hint != "auto" and doc_type_hint in SUPPORTED_TYPES:
            doc_type = doc_type_hint
        else:
            doc_type = classify_document_type(ocr_text)
        result["document_type"] = doc_type

        logger.info("Step 4: VLM extraction")
        vlm_output = extract_with_vlm(primary_image, doc_type)
        if "error" in vlm_output:
            logger.warning(f"VLM failed: {vlm_output['error']}")
            vlm_output = {}

        logger.info("Step 5: Rule-based extraction")
        rule_output = rule_based_extraction(ocr_text, doc_type)

        logger.info("Step 6: Merging with confidence")
        merged_fields = {}
        all_fields = set(list(vlm_output.keys()) + list(rule_output.keys()))

        for field in all_fields:
            if field in ("line_items", "items", "transactions"):
                continue

            vlm_val = vlm_output.get(field)
            rule_val = rule_output.get(field)
            final_value = vlm_val if vlm_val is not None else rule_val

            confidence = calculate_field_confidence(
                field_name=field,
                ocr_value=None,
                vlm_value=vlm_val,
                rule_value=rule_val,
                validation_passed=True
            )

            merged_fields[field] = {
                "value": final_value,
                "confidence": round(confidence, 3),
                "requires_review": requires_review(confidence),
                "source": "vlm" if vlm_val is not None else "rule"
            }

            if requires_review(confidence):
                result["requires_review"] = True

        result["fields"] = merged_fields
        result["line_items"] = (
            vlm_output.get("line_items")
            or vlm_output.get("items")
            or vlm_output.get("transactions")
            or []
        )

        logger.info("Step 7: Final validation")
        flat_data = {k: v["value"] for k, v in merged_fields.items()}
        flat_data["line_items"] = result["line_items"]
        result["validation"] = validate_extracted_data(flat_data, doc_type)

        if not result["validation"]["valid"]:
            result["requires_review"] = True

        result["page_count"] = len(image_paths)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        result["status"] = "failed"
        result["error"] = str(e)

    return result