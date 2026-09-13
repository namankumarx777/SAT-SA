from __future__ import annotations

from app.analytics.execution_gap.evidence import execution_finding, feature_evidence


def test_execution_gap_evidence_is_linked_to_entity_feature() -> None:
    finding = execution_finding(
        detector_id="EG001", entity_id="E1", finding_type="Execution Gap", severity="High", confidence="Medium",
        title="Potential gap", summary="Summary", rationale="Rationale", metric_name="rate", observed=0.3,
        expected=0.6, population_size=10, absolute_gap=0.3, relative_gap=0.5,
        baseline_method="configured_supervisory_expectation",
    )
    evidence = feature_evidence(finding, "E1", ["critical_case_count", "critical_escalation_rate"], {"critical_case_count": 10, "critical_escalation_rate": 0.3})
    assert finding.rule_id == "EG001"
    assert finding.absolute_gap == 0.3
    assert finding.baseline_method == "configured_supervisory_expectation"
    assert finding.baseline_type == "configured_expectation"
    assert finding.baseline_value == 0.6
    assert finding.gap_value == 0.3
    assert finding.gap_direction == "lower_is_gap"
    assert finding.evidence_strength == "Medium"
    assert finding.confidence_type == "evidence_strength"
    assert len(evidence) == 2
    assert all(item.finding_id == finding.id and item.entity_id == "E1" for item in evidence)
