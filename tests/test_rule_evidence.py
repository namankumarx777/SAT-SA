from __future__ import annotations

from app.analytics.rules.evidence import evidence_id, make_evidence, make_finding, stable_id


def test_finding_and_evidence_ids_are_deterministic_and_traceable() -> None:
    finding = make_finding(
        rule_id="R001", entity_id="CSE-001", source_id="CASE-1", finding_type="Rapid Closure",
        severity="Medium", confidence="High", title="Title", summary="Summary", rationale="Rationale",
    )
    duplicate = make_finding(
        rule_id="R001", entity_id="CSE-001", source_id="CASE-1", finding_type="Rapid Closure",
        severity="Medium", confidence="High", title="Title", summary="Summary", rationale="Rationale",
    )
    evidence = make_evidence(finding, "case_feature", "CASE-1", "investigation_minutes", 4.0, "duration")
    assert finding.id == duplicate.id == stable_id("R001", "CSE-001", "CASE-1")
    assert evidence.finding_id == finding.id
    assert evidence.id == evidence_id(finding.id, "case_feature", "CASE-1", "investigation_minutes")
    assert "risk_score" not in finding.model_dump()
