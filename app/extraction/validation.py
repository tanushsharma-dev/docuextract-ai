from __future__ import annotations


def validate_extraction(payload: dict) -> dict:
    issues = []
    if not payload.get("vendor"):
        issues.append("Missing vendor")
    return {"valid": not issues, "issues": issues}
