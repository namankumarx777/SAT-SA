from __future__ import annotations

from pydantic import BaseModel, Field

from app.analytics.detectors.models import Confidence, Evidence, Finding, FindingType, Severity

__all__ = ["Confidence", "Evidence", "Finding", "FindingType", "Severity"]


class RuleDefinition(BaseModel):
    rule_id: str
    name: str
    description: str
    finding_type: FindingType
    severity: Severity
    enabled: bool = True
    version: str = "1.0"
    thresholds: dict[str, float | int] = Field(default_factory=dict)


class RuleRunResult(BaseModel):
    findings: list[Finding]
    evidence: list[Evidence]
    rules_evaluated: list[str]
