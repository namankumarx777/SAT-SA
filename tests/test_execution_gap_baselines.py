from __future__ import annotations

import polars as pl

from app.analytics.execution_gap.baselines import confidence_for_gap, configured_baseline, population_median


def test_configured_and_population_median_baselines() -> None:
    configured = configured_baseline(0.60)
    assert configured.value == 0.60
    assert configured.method == "configured_supervisory_expectation"
    frame = pl.DataFrame({"metric": [0.60, 0.65, 0.70, 0.90], "population": [5, 5, 5, 5]})
    baseline = population_median(frame, "metric", "population", 5)
    assert baseline.value == 0.675
    assert baseline.method == "population_median"
    assert population_median(frame, "metric", "population", 10).value is None


def test_confidence_is_deterministic_and_gap_sensitive() -> None:
    assert confidence_for_gap(5, 0.10) == "Low"
    assert confidence_for_gap(10, 0.15) == "Medium"
    assert confidence_for_gap(20, 0.25) == "High"
