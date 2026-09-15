from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.analytics.detectors.models import Evidence, Finding


class NegativeSpaceDefinition(BaseModel):
    detector_id: str
    name: str
    description: str
    severity: Literal["Low", "Medium", "High", "Critical"]
    enabled: bool = True
    version: str = "1.0"
    data_requirements: list[str] = Field(default_factory=list)
    expectation_method: str
    minimum_population: int = 0
    thresholds: dict[str, float | int] = Field(default_factory=dict)
    deferred_reason: str | None = None


class ObservationWindow(BaseModel):
    start: str | None
    end: str | None
    sufficient: bool
    reason: str | None = None


class NegativeSpaceRunResult(BaseModel):
    findings: list[Finding]
    evidence: list[Evidence]
    detectors_evaluated: list[str]
    deferred_detectors: dict[str, str] = Field(default_factory=dict)
    observation_window: ObservationWindow
