from __future__ import annotations


def compute_confidence(model_score: float, rule_score: float) -> float:
    return round(max(0.0, min(1.0, (model_score + rule_score) / 2.0)), 4)
