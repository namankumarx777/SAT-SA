from __future__ import annotations

from app.analytics.peer_anomaly.evidence import anomaly_finding, peer_finding


def test_peer_and_anomaly_finding_metadata_is_explicit() -> None:
    peer = peer_finding(detector_id="PB001", entity_id="E1", metric="critical_escalation_rate", observed=0.2, median=0.6, deviation=0.4, peer_count=3, cohort_key="Energy|Small|High", strength="Medium", title="Peer deviation", rationale="Peer reference.")
    anomaly = anomaly_finding(entity_id="E1", score=-0.2, rank=1, contributions=[{"feature": "alert_count", "observed_value": 10, "reference_value": 2}], strength="Medium", rationale="Contributing deviation.")
    assert peer.baseline_type == "peer_reference" and peer.reference_value == 0.6
    assert anomaly.anomaly_score == -0.2 and anomaly.contributing_deviations
    assert "risk_score" not in anomaly.model_dump()
