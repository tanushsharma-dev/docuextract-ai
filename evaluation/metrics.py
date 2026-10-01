import re
from typing import Dict, List

def normalized_match(pred, truth) -> bool:
    def normalize(s):
        if s is None:
            return ""
        s = str(s).lower().strip()
        s = re.sub(r'[^\w\s]', '', s)
        return re.sub(r'\s+', ' ', s)
    return normalize(pred) == normalize(truth)

def compute_field_metrics(predictions: List[Dict], ground_truth: List[Dict]) -> Dict:
    fields = ["vendor_name", "invoice_number", "invoice_date", "total_amount"]
    results = {}
    for field in fields:
        correct = 0
        total = 0
        for pred, truth in zip(predictions, ground_truth):
            if field in truth:
                total += 1
                if normalized_match(pred.get(field), truth.get(field)):
                    correct += 1
        results[field] = {
            "accuracy": round(correct / total, 3) if total > 0 else 0,
            "correct": correct,
            "total": total
        }
    return results

def compute_line_item_f1(pred_items: List[Dict], truth_items: List[Dict]) -> Dict:
    if not truth_items:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0} if not pred_items else {"precision": 0, "recall": 0, "f1": 0}
    tp = 0
    for p in pred_items:
        for t in truth_items:
            if normalized_match(p.get("description"), t.get("description")):
                tp += 1
                break
    precision = tp / len(pred_items) if pred_items else 0
    recall = tp / len(truth_items) if truth_items else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    return {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3)}

def compute_arithmetic_accuracy(predictions: List[Dict]) -> float:
    correct = 0
    total = 0
    for pred in predictions:
        subtotal = pred.get("subtotal")
        tax = pred.get("tax", 0) or 0
        total_amt = pred.get("total_amount")
        if subtotal is not None and total_amt is not None:
            total += 1
            if abs((subtotal + tax) - total_amt) < 1.0:
                correct += 1
    return correct / total if total > 0 else 0