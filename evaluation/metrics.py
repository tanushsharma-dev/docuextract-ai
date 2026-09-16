from __future__ import annotations


def precision_score(true_positives: int, false_positives: int) -> float:
    denominator = true_positives + false_positives
    return 0.0 if denominator == 0 else true_positives / denominator


def recall_score(true_positives: int, false_negatives: int) -> float:
    denominator = true_positives + false_negatives
    return 0.0 if denominator == 0 else true_positives / denominator


def f1_score(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)
