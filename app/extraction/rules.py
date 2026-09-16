from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RuleResult:
    passed: bool
    message: str = ""


def validate_amount(value: float) -> RuleResult:
    if value < 0:
        return RuleResult(False, "Amount cannot be negative.")
    return RuleResult(True, "Amount is valid.")
