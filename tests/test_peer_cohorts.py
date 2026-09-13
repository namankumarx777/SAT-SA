from __future__ import annotations

import polars as pl

from app.analytics.peer_anomaly.cohorts import build_cohorts, cohort_key


def test_structural_cohorts_use_sector_size_and_criticality() -> None:
    frame = pl.DataFrame({"entity_id": ["E1", "E2", "E3", "E4"], "sector": ["Energy", "Energy", "Energy", "Banking"], "size": ["Small", "Small", "Small", "Small"], "criticality": ["High", "High", "High", "High"]})
    cohorts = build_cohorts(frame)
    assert len(cohorts) == 1
    assert cohorts[0].entity_ids == ["E1", "E2", "E3"]
    assert cohort_key(frame.row(0, named=True)) == "Energy|Small|High"
