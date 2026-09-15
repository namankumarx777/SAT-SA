from __future__ import annotations

from pydantic import BaseModel, Field

from app.analytics.detectors.models import Evidence, Finding


class Cohort(BaseModel):
    key: str
    sector: str
    size: str
    criticality: str
    entity_ids: list[str]


class PeerStatistic(BaseModel):
    metric_name: str
    cohort_key: str
    peer_count: int
    peer_median: float
    peer_mean: float
    peer_std: float
    peer_p25: float
    peer_p75: float


class PeerAnomalyRunResult(BaseModel):
    findings: list[Finding]
    evidence: list[Evidence]
    cohort_count: int
    entities_benchmarked: int
    anomalies: int
    deferred_detectors: dict[str, str] = Field(default_factory=dict)
