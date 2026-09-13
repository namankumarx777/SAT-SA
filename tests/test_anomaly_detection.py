from __future__ import annotations

import polars as pl

from app.analytics.peer_anomaly.anomaly import detect_anomalies


def test_anomaly_detector_defers_small_population_and_is_deterministic() -> None:
    small = pl.DataFrame({"entity_id": ["E1"] * 3, "alert_count": [1, 2, 3]})
    assert detect_anomalies(small)[0].height == 0
    frame = pl.DataFrame({"entity_id": [f"E{i:02d}" for i in range(12)], "alert_count": list(range(1, 13)), "case_count": list(range(1, 13)), "alerts_per_asset": [float(i) for i in range(1, 13)]})
    first, features = detect_anomalies(frame)
    second, _ = detect_anomalies(frame)
    assert features
    assert first.equals(second)
    assert first.height > 0
