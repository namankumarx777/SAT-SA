from __future__ import annotations

import pytest

from app.analytics.supervisory_risk.config import DIMENSION_WEIGHTS
from app.analytics.supervisory_risk.correlation import (
    build_risk_contributions,
    evaluate_correlation_groups,
)
from app.analytics.supervisory_risk.normalization import NormalizedSignal


def test_escalation_correlation_prevents_quadruple_counting() -> None:
    entity_id = "CSE-CORR-TEST"

    # Case A: Only EG001 (Phase 6 Execution Gap alone)
    signal_eg001 = NormalizedSignal(
        entity_id=entity_id, detector_id="EG001", source_phase="phase6",
        signal_name="Critical Escalation Gap", raw_value=0.30, normalized_value=50.0,
        severity="High", evidence_strength="High", assessment_strength="High",
        supporting_finding_ids=["f_eg001"],
    )
    groups_single = evaluate_correlation_groups(entity_id, [signal_eg001])
    assert len(groups_single) == 1
    assert groups_single[0].base_value == 50.0
    assert groups_single[0].final_value == 50.0
    assert groups_single[0].corroboration_level == "Single Phase"

    # Case B: All 4 detectors trigger for the same issue: R002, EG001, PB001, AN001 (with matching critical_escalation_rate feature)
    signal_r002 = NormalizedSignal(
        entity_id=entity_id, detector_id="R002", source_phase="phase5",
        signal_name="Unescalated Critical Case Prevalence", raw_value=5, normalized_value=45.0,
        severity="High", evidence_strength=None, assessment_strength="Medium",
        supporting_finding_ids=["f_r002_1", "f_r002_2"],
    )
    signal_pb001 = NormalizedSignal(
        entity_id=entity_id, detector_id="PB001", source_phase="phase8",
        signal_name="Critical Escalation Peer Deviation", raw_value=0.25, normalized_value=40.0,
        severity="High", evidence_strength="Medium", assessment_strength="Medium",
        supporting_finding_ids=["f_pb001"],
    )
    signal_an001 = NormalizedSignal(
        entity_id=entity_id, detector_id="AN001", source_phase="phase8",
        signal_name="Unusual Operational Profile (Contextual Anomaly)", raw_value=0.6, normalized_value=18.0,
        severity="Medium", evidence_strength="Low", assessment_strength="Low",
        supporting_finding_ids=["f_an001"],
        contributing_features=["critical_escalation_rate"],
    )

    all_four_signals = [signal_eg001, signal_r002, signal_pb001, signal_an001]
    groups_corroborated = evaluate_correlation_groups(entity_id, all_four_signals)

    # CRITICAL VERIFICATION:
    # 1. Should produce correlation groups: CRITICAL_ESCALATION and ANOMALY_PROFILE
    esc_groups = [g for g in groups_corroborated if g.group_id == "CRITICAL_ESCALATION"]
    assert len(esc_groups) == 1
    esc_group = esc_groups[0]

    # 2. Base score must be the primary signal (50.0), NOT 50 + 45 + 40 + 18 = 153!
    assert esc_group.base_value == 50.0

    # 3. Summing naively would produce 153.0.
    # Our corroboration model applies a bounded boost (+24% for 3 distinct phases: phase5, phase6, phase8)
    # Expected final score: 50 * (1 + 0.24) = 62.0
    naive_sum = 50.0 + 45.0 + 40.0 + 18.0
    assert esc_group.final_value < naive_sum
    assert esc_group.final_value == 62.0  # 50.0 + 24% boost

    # 4. Corroboration level must be Strong (3 distinct phases)
    assert esc_group.corroboration_level == "Strong"
    assert set(esc_group.corroborating_phases) == {"phase5", "phase6", "phase8"}

    # 5. All 5 supporting finding IDs are captured
    assert set(esc_group.supporting_finding_ids) == {"f_eg001", "f_r002_1", "f_r002_2", "f_pb001", "f_an001"}

    # 6. Contributions must produce only 1 contribution record for this group
    contribs = build_risk_contributions(entity_id, groups_corroborated, DIMENSION_WEIGHTS)
    esc_contribs = [c for c in contribs if c.corroboration_group == "CRITICAL_ESCALATION"]
    assert len(esc_contribs) == 1
    assert esc_contribs[0].normalized_value == 62.0


def test_investigation_and_remediation_correlation() -> None:
    entity_id = "CSE-INV-REM"

    # Remediation: R003 (phase5) + EG003 (phase6)
    sig_r003 = NormalizedSignal(
        entity_id=entity_id, detector_id="R003", source_phase="phase5",
        signal_name="Unremediated Assets", raw_value=3, normalized_value=30.0,
        severity="Medium", evidence_strength=None, assessment_strength="Medium",
        supporting_finding_ids=["f_r003"],
    )
    sig_eg003 = NormalizedSignal(
        entity_id=entity_id, detector_id="EG003", source_phase="phase6",
        signal_name="Remediation Gap", raw_value=0.20, normalized_value=40.0,
        severity="High", evidence_strength="High", assessment_strength="High",
        supporting_finding_ids=["f_eg003"],
    )

    groups = evaluate_correlation_groups(entity_id, [sig_r003, sig_eg003])
    rem_groups = [g for g in groups if g.group_id == "REMEDIATION"]
    assert len(rem_groups) == 1
    # 2 distinct phases -> Moderate corroboration (+12% boost to base 40.0 = 44.8)
    assert rem_groups[0].base_value == 40.0
    assert rem_groups[0].final_value == 44.8
    assert rem_groups[0].corroboration_level == "Moderate"


def test_an001_isolation_single_feature() -> None:
    """A single AN001 finding with only critical_escalation_rate must NOT create Monitoring, Remediation, or Investigation signals."""
    entity_id = "CSE-ISOLATION"
    sig_an001 = NormalizedSignal(
        entity_id=entity_id, detector_id="AN001", source_phase="phase8",
        signal_name="Unusual Operational Profile", raw_value=0.8, normalized_value=20.0,
        severity="Medium", evidence_strength="Low", assessment_strength="Low",
        supporting_finding_ids=["f_an001"],
        contributing_features=["critical_escalation_rate"],
    )

    groups = evaluate_correlation_groups(entity_id, [sig_an001])
    group_ids = {g.group_id for g in groups}

    # Must participate in CRITICAL_ESCALATION and ANOMALY_PROFILE
    assert "CRITICAL_ESCALATION" in group_ids
    assert "ANOMALY_PROFILE" in group_ids

    # MUST NOT participate in MONITORING_COVERAGE, REMEDIATION, INVESTIGATION_EFFORT, RAPID_CLOSURE, ACTIVITY_VOLATILITY
    assert "MONITORING_COVERAGE" not in group_ids
    assert "REMEDIATION" not in group_ids
    assert "INVESTIGATION_EFFORT" not in group_ids
    assert "RAPID_CLOSURE" not in group_ids
    assert "ACTIVITY_VOLATILITY" not in group_ids


def test_an001_multi_feature_behavior() -> None:
    """If AN001 contains critical_escalation_rate and remediation_rate, it corroborates both dimensions, but not unrelated ones."""
    entity_id = "CSE-MULTI"
    sig_an001 = NormalizedSignal(
        entity_id=entity_id, detector_id="AN001", source_phase="phase8",
        signal_name="Unusual Operational Profile", raw_value=0.8, normalized_value=20.0,
        severity="Medium", evidence_strength="Low", assessment_strength="Low",
        supporting_finding_ids=["f_an001"],
        contributing_features=["critical_escalation_rate", "remediation_rate"],
    )

    groups = evaluate_correlation_groups(entity_id, [sig_an001])
    group_ids = {g.group_id for g in groups}

    assert "CRITICAL_ESCALATION" in group_ids
    assert "REMEDIATION" in group_ids
    assert "ANOMALY_PROFILE" in group_ids
    assert "MONITORING_COVERAGE" not in group_ids
    assert "INVESTIGATION_EFFORT" not in group_ids
    assert "RAPID_CLOSURE" not in group_ids


def test_an001_no_phantom_corroboration_in_unrelated_group() -> None:
    """AN001 without monitoring features must not increase corroboration count or boost for MONITORING_COVERAGE."""
    entity_id = "CSE-PHANTOM"
    sig_r005 = NormalizedSignal(
        entity_id=entity_id, detector_id="R005", source_phase="phase5",
        signal_name="Unmonitored Critical Assets", raw_value=2, normalized_value=40.0,
        severity="High", evidence_strength=None, assessment_strength="High",
        supporting_finding_ids=["f_r005"],
    )
    sig_an001 = NormalizedSignal(
        entity_id=entity_id, detector_id="AN001", source_phase="phase8",
        signal_name="Unusual Operational Profile", raw_value=0.8, normalized_value=20.0,
        severity="Medium", evidence_strength="Low", assessment_strength="Low",
        supporting_finding_ids=["f_an001"],
        contributing_features=["critical_escalation_rate"],  # Not monitoring!
    )

    groups = evaluate_correlation_groups(entity_id, [sig_r005, sig_an001])
    mon_group = next(g for g in groups if g.group_id == "MONITORING_COVERAGE")

    # Corroboration should remain Single Phase (only phase5 from R005, NOT phase8 from AN001)
    assert mon_group.corroboration_level == "Single Phase"
    assert mon_group.final_value == 40.0
    assert mon_group.corroborating_phases == ["phase5"]
    assert "AN001" not in mon_group.participating_detectors
