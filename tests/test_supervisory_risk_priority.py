from __future__ import annotations

import pytest

from app.analytics.supervisory_risk.correlation import CorrelatedGroupSignal
from app.analytics.supervisory_risk.inputs import (
    StandardizedEvidence,
    StandardizedFinding,
)
from app.analytics.supervisory_risk.models import EntityRisk
from app.analytics.supervisory_risk.priority import build_review_queue


def test_systemic_execution_gap_outranks_scattered_low_severity_noise() -> None:
    # Entity A: Has 1 systemic Phase 6 execution gap (EG001)
    entity_a_risk = EntityRisk(
        entity_id="CSE-SYSTEMIC",
        escalation_score=50.0, investigation_score=0.0, remediation_score=0.0,
        monitoring_score=0.0, operational_discipline_score=0.0, cyber_resilience_score=0.0,
        overall_score=12.5,  # 50 * 0.25 = 12.5 (Low overall risk scalar)
        risk_band="LOW", assessment_coverage=1.0, assessable_dimensions=6, total_dimensions=6,
        evidence_strength_summary="High: 1", corroboration_summary="Single phase",
        top_risk_dimension="Escalation", top_reason="Critical escalation execution gap",
        supporting_finding_count=1,
    )
    finding_systemic = StandardizedFinding(
        id="f_eg001", rule_id="EG001", entity_id="CSE-SYSTEMIC", source_phase="phase6",
        finding_type="Execution Gap", severity="High", confidence="High",
        evidence_strength="High", confidence_type="evidence_strength",
        title="Critical Escalation Execution Gap", summary="Gap", rationale="Gap",
        status="OPEN", created_at="2025-01-01", gap_value=0.30, baseline_value=0.60,
    )

    # Entity B: Has 15 minor record-level findings in Phase 5
    entity_b_risk = EntityRisk(
        entity_id="CSE-NOISY",
        escalation_score=15.0, investigation_score=15.0, remediation_score=15.0,
        monitoring_score=10.0, operational_discipline_score=0.0, cyber_resilience_score=0.0,
        overall_score=15.0,  # Slightly higher scalar risk score (15.0 vs 12.5)
        risk_band="LOW", assessment_coverage=1.0, assessable_dimensions=6, total_dimensions=6,
        evidence_strength_summary="Unannotated: 15", corroboration_summary="No multi-phase",
        top_risk_dimension="Escalation", top_reason="Minor records",
        supporting_finding_count=15,
    )
    minor_findings = [
        StandardizedFinding(
            id=f"f_r001_{i}", rule_id="R001", entity_id="CSE-NOISY", source_phase="phase5",
            finding_type="Rapid Closure", severity="Medium", confidence="Medium",
            evidence_strength=None, confidence_type=None, title="Rapid closure",
            summary="Case closed fast", rationale="Short", status="OPEN", created_at="2025-01-01",
        )
        for i in range(15)
    ]

    findings_by_entity = {
        "CSE-SYSTEMIC": [finding_systemic],
        "CSE-NOISY": minor_findings,
    }

    queue = build_review_queue(
        entity_risks=[entity_a_risk, entity_b_risk],
        group_signals_by_entity={},
        findings_by_entity=findings_by_entity,
        evidence_by_finding={},
    )

    # In the review queue, Entity A's systemic execution gap and entity review item must outrank Entity B!
    # Finding queue item for EG001 should be prioritized
    top_queue_item = queue[0]
    assert top_queue_item.entity_id == "CSE-SYSTEMIC"
    assert top_queue_item.priority == "HIGH"
    assert top_queue_item.record_id == "f_eg001" or top_queue_item.record_id == "CSE-SYSTEMIC"

    # Verify risk != review_priority conceptually and numerically
    # Entity B has higher overall_score (15.0 vs 12.5), but Entity A has higher priority!
    systemic_entity_item = next(q for q in queue if q.record_id == "CSE-SYSTEMIC" and q.record_type == "ENTITY")
    noisy_entity_item = next(q for q in queue if q.record_id == "CSE-NOISY" and q.record_type == "ENTITY")
    assert systemic_entity_item.priority_score > noisy_entity_item.priority_score


def test_review_queue_traceability() -> None:
    entity_id = "CSE-TRACE"
    finding = StandardizedFinding(
        id="finding_123", rule_id="EG001", entity_id=entity_id, source_phase="phase6",
        finding_type="Execution Gap", severity="High", confidence="High",
        evidence_strength="High", confidence_type="evidence_strength",
        title="Critical Escalation Gap", summary="Gap", rationale="Gap",
        status="OPEN", created_at="2025-01-01", gap_value=0.25, baseline_value=0.60,
    )
    evidence = StandardizedEvidence(
        id="ev_456", finding_id="finding_123", source_type="case_feature",
        source_id="case_001", entity_id=entity_id, field="is_escalated",
        value=False, reason="Critical case was not escalated",
    )
    risk = EntityRisk(
        entity_id=entity_id,
        escalation_score=40.0, investigation_score=0.0, remediation_score=0.0,
        monitoring_score=0.0, operational_discipline_score=0.0, cyber_resilience_score=0.0,
        overall_score=10.0, risk_band="LOW", assessment_coverage=1.0,
        assessable_dimensions=6, total_dimensions=6, evidence_strength_summary="High: 1",
        corroboration_summary="None", top_risk_dimension="Escalation",
        top_reason="Escalation gap", supporting_finding_count=1,
    )

    queue = build_review_queue(
        entity_risks=[risk],
        group_signals_by_entity={},
        findings_by_entity={entity_id: [finding]},
        evidence_by_finding={"finding_123": [evidence]},
    )

    # Queue contains items with supporting finding IDs
    assert len(queue) > 0
    item = queue[0]
    assert "finding_123" in item.supporting_finding_ids
    # Finding links to evidence
    assert evidence.finding_id == item.supporting_finding_ids[0]
