from __future__ import annotations

from datetime import datetime

import polars as pl

from app.analytics.features.asset_features import build_asset_features


def test_asset_activity_monitoring_and_recency_features() -> None:
    assets = pl.DataFrame({
        "id": ["AS1", "AS2"], "entity_id": ["E1", "E1"], "asset_type": ["Server", "Database"],
        "criticality": ["High", "Critical"], "expected_monitoring": [True, True], "monitoring_source": ["EDR", "Cloud Security"],
    })
    alerts = pl.DataFrame({
        "id": ["A1", "A2"], "entity_id": ["E1", "E1"], "asset_id": ["AS1", "AS1"],
        "timestamp": [datetime(2025, 1, 1), datetime(2025, 1, 10)], "severity": ["High", "Critical"],
        "source": ["EDR", "EDR"], "acknowledged_at": [None, None], "closed_at": [None, None],
        "status": ["Open", "Open"], "case_id": [None, None],
    })
    cases = pl.DataFrame({"id": [], "entity_id": [], "alert_id": [], "opened_at": [], "closed_at": [], "investigation_text": [], "disposition": [], "escalated": [], "remediation_recorded": []}, schema={"id": pl.String, "entity_id": pl.String, "alert_id": pl.String, "opened_at": pl.Datetime, "closed_at": pl.Datetime, "investigation_text": pl.String, "disposition": pl.String, "escalated": pl.Boolean, "remediation_recorded": pl.Boolean})
    features = build_asset_features(assets, alerts, cases).sort("id")
    assert features["alert_count"].to_list() == [2, 0]
    assert features["has_alert_activity"].to_list() == [True, False]
    assert features["expected_monitoring_no_activity"].to_list() == [False, True]
    assert features["days_since_last_alert"].to_list() == [0.0, None]
