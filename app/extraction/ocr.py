from paddleocr import PaddleOCR
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# Initialize PaddleOCR once
_ocr_instance = None

def get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = PaddleOCR(
            use_angle_cls=True,
            lang='en',
            use_gpu=False,
            show_log=False
        )
    return _ocr_instance

def run_ocr(image_path: str) -> Dict:
    """Run OCR on image and return structured output."""
    ocr = get_ocr()
    result = ocr.ocr(image_path, cls=True)

    tokens = []
    full_text = []

    if result and result[0]:
        for line in result[0]:
            bbox, (text, confidence) = line
            tokens.append({
                "text": text,
                "confidence": float(confidence),
                "bbox": {
                    "x_min": int(bbox[0][0]),
                    "y_min": int(bbox[0][1]),
                    "x_max": int(bbox[2][0]),
                    "y_max": int(bbox[2][1])
                }
            })
            full_text.append(text)

    return {
        "tokens": tokens,
        "full_text": " ".join(full_text),
        "token_count": len(tokens),
        "avg_confidence": sum(t["confidence"] for t in tokens) / max(len(tokens), 1)
    }

def extract_text_blocks(ocr_result: Dict) -> List[Dict]:
    """Group tokens into text blocks based on proximity."""
    tokens = ocr_result["tokens"]
    if not tokens:
        return []

    # Sort by y then x
    sorted_tokens = sorted(tokens, key=lambda t: (t["bbox"]["y_min"], t["bbox"]["x_min"]))

    blocks = []
    current_block = {
        "tokens": [sorted_tokens[0]],
        "y_center": (sorted_tokens[0]["bbox"]["y_min"] + sorted_tokens[0]["bbox"]["y_max"]) / 2
    }

    for token in sorted_tokens[1:]:
        y_center = (token["bbox"]["y_min"] + token["bbox"]["y_max"]) / 2
        # Same line if y difference < 15 pixels
        if abs(y_center - current_block["y_center"]) < 15:
            current_block["tokens"].append(token)
        else:
            blocks.append(current_block)
            current_block = {
                "tokens": [token],
                "y_center": y_center
            }
    blocks.append(current_block)

    # Format blocks
    formatted = []
    for block in blocks:
        texts = [t["text"] for t in block["tokens"]]
        formatted.append({
            "text": " ".join(texts),
            "tokens": block["tokens"],
            "avg_confidence": sum(t["confidence"] for t in block["tokens"]) / len(block["tokens"])
        })

    return formatted