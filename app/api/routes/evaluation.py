from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.get("/metrics")
def get_evaluation_metrics():
    return {
        "precision": 0.0,
        "recall": 0.0,
        "f1_score": 0.0,
        "samples": 0,
    }
