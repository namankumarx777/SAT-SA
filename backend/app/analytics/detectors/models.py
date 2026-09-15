from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

FindingType = Literal["Rapid Closure", "Escalation", "Repeated Activity", "Investigation", "Monitoring Coverage", "Execution Gap", "Critical Asset Inactivity", "Alert Source Coverage", "Low Activity", "Missing Investigation", "Missing Escalation Evidence", "Peer Deviation", "Unknown Anomaly"]
Severity = Literal["Low", "Medium", "High", "Critical"]
Confidence = Literal["Low", "Medium", "High"]


class Finding(BaseModel):
    id: str
    rule_id: str
    entity_id: str
    finding_type: FindingType
    severity: Severity
    confidence: Confidence
    evidence_strength: Confidence | None = None
    confidence_type: Literal["evidence_strength"] | None = None
    title: str
    summary: str
    rationale: str
    status: Literal["OPEN"] = "OPEN"
    created_at: datetime
    metric_name: str | None = None
    observed_value: float | int | str | None = None
    expected_value: float | int | str | None = None
    threshold: float | int | str | None = None
    population_size: int | None = None
    absolute_gap: float | None = None
    relative_gap: float | None = None
    baseline_method: str | None = None
    baseline_type: str | None = None
    baseline_value: float | None = None
    reference_value: float | None = None
    gap_value: float | None = None
    gap_direction: str | None = None
    anomaly_score: float | None = None
    anomaly_rank: int | None = None
    contributing_deviations: list[dict[str, Any]] | None = None


class Evidence(BaseModel):
    id: str
    finding_id: str
    source_type: str
    source_id: str
    entity_id: str
    field: str
    value: Any
    reason: str