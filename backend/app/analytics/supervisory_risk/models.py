from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


RiskBand = Literal["LOW", "MODERATE", "HIGH", "CRITICAL"]
PriorityLevel = Literal["HIGH", "MEDIUM", "LOW"]
RecordType = Literal["ENTITY", "FINDING", "CASE", "ALERT", "ASSET"]


class RiskContribution(BaseModel):
    id: str
    entity_id: str
    dimension: str
    source_phase: str
    detector_id: str
    signal_name: str
    raw_value: float | int | str | None = None
    normalized_value: float = Field(ge=0.0, le=100.0)
    weight: float = Field(ge=0.0)
    contribution: float = Field(ge=0.0)
    severity: str
    evidence_strength: str | None = None
    assessment_strength: str = "Medium"
    corroboration_group: str
    supporting_finding_ids: list[str] = Field(default_factory=list)
    rationale: str


class EntityRisk(BaseModel):
    entity_id: str
    escalation_score: float | None = Field(default=None, ge=0.0, le=100.0)
    investigation_score: float | None = Field(default=None, ge=0.0, le=100.0)
    remediation_score: float | None = Field(default=None, ge=0.0, le=100.0)
    monitoring_score: float | None = Field(default=None, ge=0.0, le=100.0)
    operational_discipline_score: float | None = Field(default=None, ge=0.0, le=100.0)
    cyber_resilience_score: float | None = Field(default=None, ge=0.0, le=100.0)
    overall_score: float = Field(ge=0.0, le=100.0)
    risk_band: RiskBand
    assessment_coverage: float = Field(ge=0.0, le=1.0)
    assessable_dimensions: int = 6
    total_dimensions: int = 6
    evidence_strength_summary: str
    corroboration_summary: str
    top_risk_dimension: str
    top_reason: str
    supporting_finding_count: int


class ReviewQueueItem(BaseModel):
    rank: int = Field(ge=1)
    entity_id: str
    record_type: RecordType = "ENTITY"
    record_id: str
    priority: PriorityLevel
    priority_score: float = Field(ge=0.0, le=100.0)
    reason: str
    supporting_finding_ids: list[str] = Field(default_factory=list)
    evidence_strength: str | None = None


class SupervisoryRiskRunResult(BaseModel):
    entity_risks: list[EntityRisk]
    risk_contributions: list[RiskContribution]
    review_queue: list[ReviewQueueItem]
    entities_evaluated: list[str]
    detectors_consumed: list[str]
    detectors_excluded: dict[str, str] = Field(default_factory=dict)
