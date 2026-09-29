from typing import Dict, Any

def calculate_field_confidence(
    field_name: str,
    ocr_value: Any,
    vlm_value: Any,
    rule_value: Any,
    validation_passed: bool
) -> float:
    """Calculate confidence score for a field."""
    score = 0.0
    signals = 0

    # VLM signal (weight: 0.40)
    if vlm_value is not None:
        score += 0.40
        signals += 1

    # OCR/Rule signal (weight: 0.35)
    if rule_value is not None or ocr_value is not None:
        score += 0.35
        signals += 1

    # Agreement signal (weight: 0.15)
    values = [v for v in [vlm_value, rule_value, ocr_value] if v is not None]
    if len(values) >= 2:
        # Normalize and compare
        str_values = [str(v).strip().lower() for v in values]
        if len(set(str_values)) == 1:
            score += 0.15
            signals += 1

    # Validation signal (weight: 0.10)
    if validation_passed:
        score += 0.10
        signals += 1

    return min(score, 1.0)

def requires_review(confidence: float, threshold: float = 0.60) -> bool:
    return confidence < threshold

def auto_approve(confidence: float, threshold: float = 0.85) -> bool:
    return confidence >= threshold