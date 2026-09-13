from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.analytics.rules.evidence import make_evidence, make_finding
from app.analytics.rules.models import Evidence, Finding
from app.analytics.negative_space.definitions import MAX_EVIDENCE_PER_FINDING


def negative_finding(*, detector_id: str, entity_id: str, source_id: str, finding_type: str, severity: str, strength: str, title: str, summary: str, rationale: str, observed: float | int | str | None, expected: float | int | str | None, population: int, method: str, baseline_type: str, baseline_value: float | None = None, gap: float | None = None) -> Finding:
    return make_finding(
        rule_id=detector_id, entity_id=entity_id, source_id=source_id, finding_type=finding_type,
        severity=severity, confidence=strength, evidence_strength=strength, title=title, summary=summary,
        rationale=rationale, observed_value=observed, expected_value=expected, population_size=population,
        baseline_method=method, baseline_type=baseline_type, baseline_value=baseline_value,
        gap_value=gap, gap_direction="absence",
    )


def add_evidence(finding: Finding, source_type: str, source_id: str, fields: Iterable[str], row: dict[str, Any], reason: str) -> list[Evidence]:
    return [make_evidence(finding, source_type, source_id, field, row.get(field), reason) for field in fields]


def sample_rows(frame, sort_columns: list[str], limit: int = MAX_EVIDENCE_PER_FINDING) -> list[dict[str, Any]]:
    return frame.sort(sort_columns).head(limit).to_dicts()
