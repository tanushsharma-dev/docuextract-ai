"""
Extraction pipeline — orchestrates:
  1. Preprocessing (PDF → images, resize)
  2. OCR (optional, VLM handles text)
  3. Document type classification
  4. VLM extraction (parallel, fast models)
  5. Rules (field normalization)
  6. Merge + confidence scoring
  7. Validation

Returns dict shaped for worker/tasks.py:
{
  "status": "success" | "failed",
  "document_type": "invoice",
  "page_count": 4,
  "fields": {field_name: {"value", "confidence", "source", "requires_review"}},
  "line_items": [...],
  "requires_review": bool,
  "error": "..." (only if failed)
}
"""

import os
import logging

from app.extraction.preprocessing import preprocess_document
from app.extraction.vlm import (
    extract_with_vlm,
    classify_document_type,
    SUPPORTED_TYPES,
)

logger = logging.getLogger(__name__)


def run_extraction_pipeline(input_path: str, output_dir: str,
                             document_type: str = "auto") -> dict:
    """
    Main pipeline entry point.
    Called by worker/tasks.py.
    """
    logger.info("Step 1: Preprocessing")
    try:
        doc_kind, image_paths = preprocess_document(input_path, output_dir)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        return {"status": "failed", "error": f"Preprocessing error: {e}",
                "fields": {}, "line_items": [], "page_count": 0}

    if not image_paths:
        logger.error("No images produced from input")
        return {"status": "failed", "error": "No images produced",
                "fields": {}, "line_items": [], "page_count": 0}

    logger.info(f"Preprocessed into {len(image_paths)} page image(s)")

    # ============================================================
    # Step 2: OCR — skipped, VLM handles text extraction
    # ============================================================
    logger.info("Step 2: OCR")

    # ============================================================
    # Step 3: Document type
    # ============================================================
    logger.info("Step 3: Document type")
    doc_type = document_type or "auto"
    if doc_type in ("auto", "", None):
        try:
            doc_type = classify_document_type(image_paths[0])
            logger.info(f"Auto-detected document type: {doc_type}")
        except Exception as e:
            logger.warning(f"classify_document_type failed: {e} — defaulting to invoice")
            doc_type = "invoice"

    # Safety net — ensure doc_type is valid
    if doc_type not in SUPPORTED_TYPES:
        doc_type = "invoice"

    # ============================================================
    # Step 4: VLM extraction (parallel, fast models)
    # ============================================================
    logger.info("Step 4: VLM extraction")
    try:
        vlm_result = extract_with_vlm(image_paths, doc_type)
    except Exception as e:
        logger.error(f"VLM extraction crashed: {e}")
        return {"status": "failed", "error": f"VLM error: {e}",
                "fields": {}, "line_items": [], "page_count": len(image_paths)}

    if vlm_result.get("status") == "failed":
        logger.error(f"VLM returned failed: {vlm_result.get('error')}")
        return {
            "status": "failed",
            "error": vlm_result.get("error", "VLM failed"),
            "fields": {}, "line_items": [],
            "page_count": len(image_paths),
        }

    # ============================================================
    # Step 5: Rules (field normalization / cleanup)
    # ============================================================
    logger.info("Step 5: Rules")
    raw_fields = vlm_result.get("fields", {}) or {}
    try:
        from app.extraction.rules import apply_rules
        raw_fields = apply_rules(raw_fields, doc_type)
        logger.info(f"Rules applied to {len(raw_fields)} fields")
    except ImportError:
        logger.info("rules.py not found — skipping")
    except AttributeError:
        logger.info("apply_rules not found in rules.py — skipping")
    except Exception as e:
        logger.warning(f"Rules failed: {e} — keeping raw fields")

    # ============================================================
    # Step 6: Merge + confidence
    # Normalize each field into {value, confidence, source, requires_review}
    # ============================================================
    logger.info("Step 6: Merge + confidence")
    final_fields = {}
    for k, v in raw_fields.items():
        # Skip metadata-style keys that leak from VLM response
        if k in ("status", "document_type", "page_count", "fields",
                 "line_items", "_page", "error"):
            continue

        if isinstance(v, dict):
            val = v.get("value")
            conf = v.get("confidence", 0.5)
            source = v.get("source", "vlm")
        else:
            val = v
            conf = 0.5
            source = "vlm"

        # Skip empty values
        if val is None or val == "":
            continue

        try:
            conf = float(conf)
        except (ValueError, TypeError):
            conf = 0.5

        # Clamp confidence
        conf = max(0.0, min(1.0, conf))

        final_fields[k] = {
            "value": val,
            "confidence": conf,
            "source": source,
            "requires_review": conf < 0.7,
        }

    logger.info(f"Merged into {len(final_fields)} clean field(s)")

    # ============================================================
    # Step 7: Validation
    # ============================================================
    logger.info("Step 7: Validation")
    requires_review = any(f["requires_review"] for f in final_fields.values())

    try:
        from app.extraction.validation import validate_fields
        result = validate_fields(final_fields, doc_type)
        # Support both return shapes:
        #   (fields, requires_review) tuple  OR  fields dict
        if isinstance(result, tuple) and len(result) == 2:
            final_fields, requires_review = result
        elif isinstance(result, dict):
            final_fields = result
            requires_review = any(
                f.get("requires_review", False)
                for f in final_fields.values()
                if isinstance(f, dict)
            )
    except ImportError:
        logger.info("validation.py not found — skipping")
    except AttributeError:
        logger.info("validate_fields not found — skipping")
    except Exception as e:
        logger.warning(f"Validation failed: {e} — using unvalidated fields")

    # ============================================================
    # Return shaped result
    # ============================================================
    return {
        "status": "success",
        "document_type": vlm_result.get("document_type", doc_type),
        "page_count": vlm_result.get("page_count", len(image_paths)),
        "fields": final_fields,
        "line_items": vlm_result.get("line_items", []),
        "requires_review": bool(requires_review),
    }