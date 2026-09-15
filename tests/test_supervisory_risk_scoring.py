from __future__ import annotations

import pytest

from app.analytics.supervisory_risk.aggregation import (
    _determine_risk_band,
    aggregate_entity_risk,
)
from app.analytics.supervisory_risk.config import DIMENSION_WEIGHTS, DIMENSIONS
from app.analytics.supervisory_risk.correlation import CorrelatedGroupSignal
from app.analytics.supervisory_risk.dimensions import calculate_dimension_scores
from app.analytics.supervisory_risk.inputs import StandardizedFinding
from app.analytics.supervisory_risk.normalization import (
    NormalizedSignal,
    normalize_finding_signal,
)


def test_risk_band_boundaries() -> None:
    assert _determine_risk_band(0.0) == "LOW"
    assert _determine_risk_band(24.9) == "LOW"
    assert _determine_risk_band(25.0) == "MODERATE"
    assert _determine_risk_band(49.9) == "MODERATE"
    assert _determine_risk_band(50.0) == "HIGH"
    assert _determine_risk_band(74.9) == "HIGH"
    assert _determine_risk_band(75.0) == "CRITICAL"
    assert _determine_risk_band(100.0) == "CRITICAL"


def test_empty_findings_produces_zero_risk() -> None:
    entity_id = "CSE-EMPTY"
    meta = {
        "critical_case_count": 10,
        "closed_case_count": 20,
        "total_assets": 50,
        "alert_count": 100,
    }
    dim_scores, unassessable_dims = calculate_dimension_scores(entity_id, [], meta)
    assert len(unassessable_dims) == 0
    for dim, score in dim_scores.items():
        assert score == 0.0

    risk = aggregate_entity_risk(entity_id, dim_scores, unassessable_dims, [], [], meta)
    assert risk.overall_score == 0.0
    assert risk.risk_band == "LOW"
    assert risk.top_risk_dimension == "None"
    assert risk.assessment_coverage == 1.0


def test_missing_denominators_handled_conservatively() -> None:
    # Entity with 0 closed cases
    entity_id = "CSE-NOCASES"
    meta = {
        "critical_case_count": 0,
        "closed_case_count": 0,
        "total_assets": 0,
        "alert_count": 0,
    }
    sample_finding = StandardizedFinding(
        id="f1", rule_id="R001", entity_id=entity_id, source_phase="phase5",
        finding_type="Rapid Closure", severity="Medium", confidence="High",
        evidence_strength=None, confidence_type=None, title="Rapid Closure",
        summary="Test", rationale="Test", status="OPEN", created_at="2025-01-01",
    )
    sig = normalize_finding_signal(sample_finding, meta, [sample_finding])
    assert not sig.is_assessable
    assert sig.normalized_value == 0.0
    assert sig.unassessable_reason is not None


def test_r005_zero_denominator_handling() -> None:
    """When expected_monitored_assets == 0, R005 must be is_assessable = False, not assign artificial risk."""
    entity_id = "CSE-NOASSETS"
    meta = {
        "expected_monitored_assets": 0,
        "total_assets": 0,
    }
    sample_finding = StandardizedFinding(
        id="f_r005", rule_id="R005", entity_id=entity_id, source_phase="phase5",
        finding_type="Unmonitored Critical Assets", severity="High", confidence="High",
        evidence_strength=None, confidence_type=None, title="Unmonitored Assets",
        summary="Test", rationale="Test", status="OPEN", created_at="2025-01-01",
    )
    sig = normalize_finding_signal(sample_finding, meta, [sample_finding])
    assert not sig.is_assessable
    assert sig.normalized_value == 0.0
    assert "No expected-monitored assets defined" in (sig.unassessable_reason or "")


def test_dimension_assessability_and_weight_renormalization() -> None:
    """When a dimension has no assessable signals or 0 baseline context, it becomes unassessable (score=None) and its weight is excluded."""
    entity_id = "CSE-PARTIAL"
    # Metadata where Investigation, Monitoring, Remediation cannot be assessed
    meta = {
        "critical_case_count": 10,
        "case_count": 0,
        "closed_case_count": 0,  # Investigation unassessable
        "total_assets": 0,       # Monitoring & Remediation unassessable
        "expected_monitored_assets": 0,
        "alert_count": 100,
    }
    # Escalation signal exists
    esc_group = CorrelatedGroupSignal(
        group_id="CRITICAL_ESCALATION",
        dimension="Escalation",
        entity_id=entity_id,
        base_value=50.0,
        corroboration_boost=0.0,
        final_value=50.0,
        corroboration_level="Single Phase",
        corroborating_phases=["phase5"],
        participating_detectors=["R002"],
        supporting_finding_ids=["f_r002"],
        severity="High",
        assessment_strength="Medium",
        evidence_strength=None,
        rationale="Escalation test",
    )

    dim_scores, unassessable_dims = calculate_dimension_scores(entity_id, [esc_group], meta)

    assert "Investigation" in unassessable_dims
    assert "Monitoring" in unassessable_dims
    assert "Remediation" in unassessable_dims
    assert dim_scores["Investigation"] is None
    assert dim_scores["Monitoring"] is None
    assert dim_scores["Remediation"] is None
    assert dim_scores["Escalation"] == 50.0

    risk = aggregate_entity_risk(entity_id, dim_scores, unassessable_dims, [esc_group], [], meta)

    # Assessable dimensions: Escalation (0.25), Operational Discipline (0.10), Cyber Resilience (0.10)
    # Total assessable weight = 0.25 + 0.10 + 0.10 = 0.45
    # Escalation score = 50.0. Other assessable dimensions = 0.0
    # Expected overall_score = (50.0 * 0.25) / 0.45 = 12.5 / 0.45 = 27.78
    assert round(risk.overall_score, 2) == 27.78
    assert risk.assessment_coverage == round(3 / 6, 4)
    assert risk.investigation_score is None
    assert risk.monitoring_score is None
    assert risk.remediation_score is None
    assert risk.escalation_score == 50.0


def test_dimension_scores_and_overall_score_bounded_to_100() -> None:
    entity_id = "CSE-MAX"
    meta = {
        "critical_case_count": 10,
        "closed_case_count": 20,
        "total_assets": 50,
        "alert_count": 100,
    }
    # Create an extreme signal with huge value
    extreme_gs = CorrelatedGroupSignal(
        group_id="CRITICAL_ESCALATION",
        dimension="Escalation",
        entity_id=entity_id,
        base_value=100.0,
        corroboration_boost=0.50,  # +50%
        final_value=100.0,  # must be capped at 100
        corroboration_level="Strong",
        corroborating_phases=["phase5", "phase6", "phase8"],
        participating_detectors=["R002", "EG001", "PB001"],
        supporting_finding_ids=["f1", "f2"],
        severity="Critical",
        assessment_strength="High",
        evidence_strength="High",
        rationale="Extreme",
    )
    dim_scores, unassessable_dims = calculate_dimension_scores(entity_id, [extreme_gs], meta)
    assert (dim_scores["Escalation"] or 0.0) <= 100.0

    risk = aggregate_entity_risk(entity_id, dim_scores, unassessable_dims, [extreme_gs], [], meta)
    assert 0.0 <= risk.overall_score <= 100.0

