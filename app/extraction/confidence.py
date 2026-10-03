import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Safe read — config me na ho to default use hoga (crash nahi hoga)
AUTO_APPROVE = getattr(settings, "CONFIDENCE_AUTO_APPROVE", 0.85)
REVIEW_THRESHOLD = getattr(settings, "CONFIDENCE_REVIEW_THRESHOLD", 0.60)


def calculate_field_confidence(field_name=None, ocr_value=None, vlm_value=None,
                               rule_value=None, validation_passed=True, **kwargs):
    """
    Confidence scoring:
    - VLM + Rule match -> 0.98
    - VLM only         -> 0.92  (Auto-Approved)
    - Rule only        -> 0.60  (Needs Review)
    - Nothing          -> 0.10  (Missing)
    """
    vlm_empty = vlm_value is None or str(vlm_value).strip() in ("", "None", "null")
    rule_empty = rule_value is None or str(rule_value).strip() in ("", "None", "null")

    if not vlm_empty and not rule_empty:
        if str(vlm_value).strip().lower() == str(rule_value).strip().lower():
            confidence = 0.98
        else:
            confidence = 0.85
    elif not vlm_empty:
        confidence = 0.92
    elif not rule_empty:
        confidence = 0.60
    else:
        confidence = 0.10

    if validation_passed and confidence > 0.5:
        confidence = min(1.0, confidence + 0.02)

    return round(confidence, 3)


def requires_review(confidence):
    return confidence < AUTO_APPROVE


def document_status(fields):
    if not fields:
        return "needs_review"
    confs = [f.get("confidence", 0) for f in fields.values()]
    avg = sum(confs) / len(confs)
    return "extracted" if avg >= AUTO_APPROVE else "needs_review"