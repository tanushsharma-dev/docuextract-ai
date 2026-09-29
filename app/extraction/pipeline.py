import logging
from typing import Dict
from app.extraction.preprocessing import preprocess_document
from app.extraction.ocr import run_ocr
from app.extraction.vlm import extract_with_vlm, classify_document_type
from app.extraction.rules import rule_based_extraction
from app.extraction.validation import validate_extracted_data
from app.extraction.confidence import calculate_field_confidence, requires_review
from app.schemas.invoice import InvoiceSchema

logger = logging.getLogger(__name__)

def run_extraction_pipeline(file_path: str, output_dir: str) -> Dict:
    """Full extraction pipeline."""
    result = {
        "status": "success",
        "document_type": None,
        "fields": {},
        "line_items": [],
        "validation": {},
        "requires_review": False
    }

    try:
        # Step 1: Preprocess
        logger.info("Step 1: Preprocessing document")
        image_paths = preprocess_document(file_path, output_dir)
        if not image_paths:
            raise ValueError("No images generated from document")

        primary_image = image_paths[0]

        # Step 2: OCR
        logger.info("Step 2: Running OCR")
        ocr_result = run_ocr(primary_image)
        ocr_text = ocr_result["full_text"]

        # Step 3: Classify document type
        logger.info("Step 3: Classifying document")
        doc_type = classify_document_type(ocr_text)
        result["document_type"] = doc_type

        # Step 4: VLM extraction
        logger.info("Step 4: VLM extraction")
        vlm_output = extract_with_vlm(primary_image, doc_type)
        if "error" in vlm_output:
            logger.warning(f"VLM failed: {vlm_output['error']}")
            vlm_output = {}

        # Step 5: Rule-based extraction
        logger.info("Step 5: Rule-based extraction")
        rule_output = rule_based_extraction(ocr_text, doc_type)

        # Step 6: Merge + Confidence
        logger.info("Step 6: Merging results with confidence scoring")
        merged_fields = {}
        all_fields = set(list(vlm_output.keys()) + list(rule_output.keys()))

        for field in all_fields:
            if field == "line_items":
                continue

            vlm_val = vlm_output.get(field)
            rule_val = rule_output.get(field)

            # Prefer VLM if available, fallback to rule
            final_value = vlm_val if vlm_val is not None else rule_val

            # Validate
            temp_data = {field: final_value}
            validation = validate_extracted_data(temp_data, doc_type)

            confidence = calculate_field_confidence(
                field_name=field,
                ocr_value=None,
                vlm_value=vlm_val,
                rule_value=rule_val,
                validation_passed=validation["valid"]
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
        result["line_items"] = vlm_output.get("line_items", [])

        # Step 7: Final validation
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