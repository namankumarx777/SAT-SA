from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from app.analytics.detectors.models import Evidence, Finding

# Canonical timestamps are naive UTC values for cross-platform Polars compatibility.
RULE_EVALUATION_TIME = datetime(1970, 1, 1)


def stable_id(*parts: str) -> str:
    """Create a deterministic identifier from stable rule/source parts."""
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"F-{digest}"


def evidence_id(finding_id: str, source_type: str, source_id: str, field: str) -> str:
    digest = hashlib.sha256(f"{finding_id}|{source_type}|{source_id}|{field}".encode("utf-8")).hexdigest()[:16]
    return f"E-{digest}"


def make_finding(
    *, rule_id: str, entity_id: str, source_id: str, finding_type: str, severity: str,
    confidence: str, title: str, summary: str, rationale: str, metric_name: str | None = None,
    observed_value: float | int | str | None = None, expected_value: float | int | str | None = None,
    threshold: float | int | str | None = None, population_size: int | None = None,
    absolute_gap: float | None = None, relative_gap: float | None = None,
    baseline_method: str | None = None, baseline_type: str | None = None,
    baseline_value: float | None = None, reference_value: float | None = None,
    gap_value: float | None = None, gap_direction: str | None = None,
    evidence_strength: str | None = None,
    anomaly_score: float | None = None, anomaly_rank: int | None = None,
    contributing_deviations: list[dict[str, Any]] | None = None,
) -> Finding:
    return Finding(
        id=stable_id(rule_id, entity_id, source_id), rule_id=rule_id, entity_id=entity_id,
        finding_type=finding_type, severity=severity, confidence=confidence,
        evidence_strength=evidence_strength or confidence, confidence_type="evidence_strength",
        title=title,
        summary=summary, rationale=rationale, created_at=RULE_EVALUATION_TIME,
        metric_name=metric_name, observed_value=observed_value, expected_value=expected_value,
        threshold=threshold, population_size=population_size, absolute_gap=absolute_gap,
        relative_gap=relative_gap, baseline_method=baseline_method,
        baseline_type=baseline_type, baseline_value=baseline_value,
        reference_value=reference_value, gap_value=gap_value, gap_direction=gap_direction,
        anomaly_score=anomaly_score, anomaly_rank=anomaly_rank,
        contributing_deviations=contributing_deviations,
    )


def make_evidence(finding: Finding, source_type: str, source_id: str, field: str, value: Any, reason: str) -> Evidence:
    return Evidence(
        id=evidence_id(finding.id, source_type, source_id, field), finding_id=finding.id,
        source_type=source_type, source_id=source_id, entity_id=finding.entity_id,
        field=field, value=value, reason=reason,
    )