from __future__ import annotations

from evaluation.metrics import f1_score, precision_score, recall_score


def evaluate_predictions(predictions: list[bool], ground_truth: list[bool]) -> dict:
    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground truth must have the same length.")

    true_positives = sum(1 for actual, expected in zip(predictions, ground_truth) if actual and expected)
    false_positives = sum(1 for actual, expected in zip(predictions, ground_truth) if actual and not expected)
    false_negatives = sum(1 for actual, expected in zip(predictions, ground_truth) if not actual and expected)

    precision = precision_score(true_positives, false_positives)
    recall = recall_score(true_positives, false_negatives)
    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score(precision, recall),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }
