from __future__ import annotations

from app.analytics.negative_space.evidence import negative_finding


def test_negative_space_finding_has_cautious_type_and_metadata() -> None:
    finding = negative_finding(
        detector_id="NS001", entity_id="E1", source_id="E1", finding_type="Monitoring Coverage", severity="Medium", strength="High",
        title="Potential monitoring coverage gap", summary="Summary", rationale="Rationale", observed=5, expected=10,
        population=10, method="expected_monitoring", baseline_type="configured_expectation", baseline_value=1.0, gap=0.5,
    )
    assert finding.finding_type == "Monitoring Coverage"
    assert finding.evidence_strength == "High"
    assert finding.baseline_type == "configured_expectation"
    assert finding.gap_direction == "absence"
    assert "negative_space" not in finding.model_dump()
