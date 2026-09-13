from __future__ import annotations

import polars as pl

from app.analytics.features.entity_features import build_entity_features


def test_entity_aggregation_and_safe_rates() -> None:
    entities = pl.DataFrame({"id": ["E1", "E2"], "name": ["One", "Two"], "sector": ["Energy", "Banking"], "size": ["Small", "Small"], "criticality": ["High", "Low"], "created_at": [None, None]})
    alerts = pl.DataFrame({
        "id": ["A1", "A2"], "entity_id": ["E1", "E1"], "asset_id": ["AS1", "AS1"], "severity": ["Critical", "Low"],
        "status": ["Closed", "Open"], "case_id": ["C1", None], "is_closed": [True, False], "is_critical": [True, False],
        "is_high_or_critical": [True, False], "asset_alert_count": [2, 2],
    })
    cases = pl.DataFrame({"id": ["C1"], "entity_id": ["E1"], "severity": ["Critical"], "is_closed": [True], "is_escalated": [True], "is_remediated": [True], "investigation_minutes": [5.0]})
    assets = pl.DataFrame({"id": ["AS1", "AS2"], "entity_id": ["E1", "E2"], "criticality": ["Critical", "Low"], "expected_monitoring": [True, False], "has_alert_activity": [True, False], "alert_count": [2, 0]})
    features = build_entity_features(entities, alerts, cases, assets).sort("entity_id")
    e1 = features.filter(pl.col("entity_id") == "E1")
    e2 = features.filter(pl.col("entity_id") == "E2")
    assert e1["alert_count"].item() == 2
    assert e1["critical_escalation_rate"].item() == 1.0
    assert e1["rapid_closure_rate"].item() == 1.0
    assert e1["monitoring_coverage_rate"].item() == 1.0
    assert e2["case_rate"].item() is None
    assert e2["monitoring_coverage_rate"].item() is None
