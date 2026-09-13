from __future__ import annotations

import polars as pl

from app.analytics.peer_anomaly.benchmarks import peer_statistics
from app.analytics.peer_anomaly.statistics import material_peer_deviation


def test_peer_statistics_and_materiality() -> None:
    frame = pl.DataFrame({"entity_id": ["E1", "E2", "E3"], "sector": ["Energy"] * 3, "size": ["Small"] * 3, "criticality": ["High"] * 3, "metric": [0.2, 0.6, 0.7]})
    stats = peer_statistics(frame, "metric")
    assert stats.height == 1
    assert stats["peer_median"].item() == 0.6
    assert stats["peer_count"].item() == 3
    assert material_peer_deviation("critical_escalation_rate", 0.2, 0.6)
    assert not material_peer_deviation("critical_escalation_rate", 0.5, 0.6)
    assert material_peer_deviation("critical_median_investigation_minutes", 20, 50)
