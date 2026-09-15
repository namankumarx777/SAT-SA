from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.analytics.detectors.evidence import make_evidence, make_finding
from app.analytics.detectors.models import Evidence, Finding
from app.analytics.execution_gap.definitions import MAX_EVIDENCE_CASES


def execution_finding(
    *, detector_id: str, entity_id: str, finding_type: str, severity: str, confidence: str,
    title: str, summary: str, rationale: str, metric_name: str, observed: float,
    expected: float, population_size: int, absolute_gap: float, relative_gap: float | None,
        baseline_method: str, reference_value: float | None = None,
        gap_direction: str = "lower_is_gap",
) -> Finding:
    return make_finding(
        rule_id=detector_id, entity_id=entity_id, source_id=entity_id,
        finding_type=finding_type, severity=severity, confidence=confidence,
        title=title, summary=summary, rationale=rationale, metric_name=metric_name,
        observed_value=observed, expected_value=expected, population_size=population_size,
        absolute_gap=absolute_gap, relative_gap=relative_gap, baseline_method=baseline_method,
            baseline_type="configured_expectation", baseline_value=expected, reference_value=reference_value,
            gap_value=absolute_gap, gap_direction=gap_direction, evidence_strength=confidence,
    )


def feature_evidence(finding: Finding, entity_id: str, fields: Iterable[str], row: dict[str, Any]) -> list[Evidence]:
    return [
        make_evidence(finding, "entity_feature", entity_id, field, row.get(field), f"Entity feature {field} supports {finding.rule_id}.")
        for field in fields
    ]


def case_evidence(finding: Finding, cases: Iterable[dict[str, Any]], fields: Iterable[str]) -> list[Evidence]:
    evidence: list[Evidence] = []
    for row in list(cases)[:MAX_EVIDENCE_CASES]:
        for field in fields:
            evidence.append(make_evidence(finding, "case_feature", row["id"], field, row.get(field), f"Representative case evidence supports {finding.rule_id}."))
    return evidence
