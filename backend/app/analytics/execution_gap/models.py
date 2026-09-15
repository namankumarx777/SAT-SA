from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.analytics.detectors.models import Evidence, Finding


class ExecutionGapDefinition(BaseModel):
    detector_id: str
    name: str
    description: str
    severity: Literal["Low", "Medium", "High", "Critical"]
    enabled: bool = True
    version: str = "1.0"
    thresholds: dict[str, float | int] = Field(default_factory=dict)
    baseline_method: str
    direction: Literal["lower_is_gap", "higher_is_gap"]
    deferred_reason: str | None = None


class BaselineResult(BaseModel):
    value: float | None
    method: str
    baseline_type: Literal["configured_expectation", "reference_statistic"]
    population_size: int


class ExecutionGapRunResult(BaseModel):
    findings: list[Finding]
    evidence: list[Evidence]
    detectors_evaluated: list[str]
    deferred_detectors: dict[str, str] = Field(default_factory=dict)
