from __future__ import annotations

from datetime import datetime

import polars as pl

from app.analytics.features.alert_features import build_alert_features


def test_alert_durations_severity_and_repeat_counts() -> None:
    alerts = pl.DataFrame({
        "id": ["A1", "A2", "A3"], "entity_id": ["E1"] * 3, "asset_id": ["AS1", "AS1", "AS2"],
        "timestamp": [datetime(2025, 1, 1), datetime(2025, 1, 2), datetime(2025, 1, 1)],
        "severity": ["Critical", "Low", "High"], "source": ["EDR", "IAM", "EDR"],
        "acknowledged_at": [datetime(2025, 1, 1, 1), None, datetime(2025, 1, 1, 2)],
        "closed_at": [datetime(2025, 1, 1, 3), None, None], "status": ["Closed", "Open", "Acknowledged"],
        "case_id": ["C1", None, None],
    })
    features = build_alert_features(alerts).sort("id")
    assert features.filter(pl.col("id") == "A1")["acknowledgement_minutes"].item() == 60
    assert features.filter(pl.col("id") == "A1")["alert_lifetime_minutes"].item() == 180
    assert features.filter(pl.col("id") == "A2")["acknowledgement_minutes"].item() is None
    assert features["severity_rank"].to_list() == [4, 1, 3]
    assert features["is_critical"].to_list() == [True, False, False]
    assert features.filter(pl.col("id") == "A1")["asset_alert_count"].item() == 2
    assert features.filter(pl.col("id") == "A1")["asset_distinct_alert_sources"].item() == 2
    assert features.filter(pl.col("id") == "A1")["has_case"].item() is True
