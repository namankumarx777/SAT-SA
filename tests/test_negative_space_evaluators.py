from __future__ import annotations

from datetime import datetime

import polars as pl

from app.analytics.negative_space.baselines import observation_window
from app.analytics.negative_space.definitions import DETECTORS
from app.analytics.negative_space.evaluators import evaluate_ns001, evaluate_ns002, evaluate_ns004, evaluate_ns005


def window() -> object:
    alerts = pl.DataFrame({"timestamp": [datetime(2025, 1, 1), datetime(2025, 2, 1)]})
    return observation_window({"alert_features": alerts})


def test_ns001_requires_expected_population_and_coverage() -> None:
    assets = pl.DataFrame({"id": ["A1", "A2", "A3", "A4", "A5", "A6"], "entity_id": ["E1"] * 6, "expected_monitoring": [True] * 6, "alert_count": [0, 0, 0, 0, 0, 1]})
    entities = pl.DataFrame({"entity_id": ["E1"], "expected_monitored_assets": [6], "monitoring_coverage_rate": [1 / 6], "assets_with_alert_activity": [1], "expected_monitored_assets_with_activity": [1], "expected_monitored_assets_without_activity": [5]})
    findings, evidence = evaluate_ns001(DETECTORS["NS001"], {"asset_features": assets, "entity_features": entities}, window())
    assert len(findings) == 1 and findings[0].entity_id == "E1" and evidence
    active = assets.with_columns(pl.lit(1).alias("alert_count"))
    assert not evaluate_ns001(DETECTORS["NS001"], {"asset_features": active, "entity_features": entities.with_columns(pl.lit(1.0).alias("monitoring_coverage_rate"))}, window())[0]


def test_ns002_requires_critical_assets() -> None:
    assets = pl.DataFrame({"id": ["A1", "A2", "A3", "A4"], "entity_id": ["E1"] * 4, "criticality": ["Critical", "Critical", "Critical", "Low"], "expected_monitoring": [True] * 4, "alert_count": [0, 0, 1, 0]})
    entities = pl.DataFrame({"entity_id": ["E1"], "critical_assets": [3], "critical_assets_with_activity": [1]})
    findings, evidence = evaluate_ns002(DETECTORS["NS002"], {"asset_features": assets, "entity_features": entities}, window())
    assert len(findings) == 1 and evidence
    assert not evaluate_ns002(DETECTORS["NS002"], {"asset_features": assets.with_columns(pl.lit("Low").alias("criticality")), "entity_features": entities}, window())[0]


def test_ns004_is_self_history_only_and_requires_four_months() -> None:
    months = pl.DataFrame({"entity_id": ["E1"] * 4, "year": [2025] * 4, "month": [1, 2, 3, 4], "alert_count": [10, 12, 11, 1], "case_count": [1] * 4})
    findings, evidence = evaluate_ns004(DETECTORS["NS004"], {"entity_month_features": months}, window())
    assert len(findings) == 1 and findings[0].baseline_type == "reference_statistic" and evidence
    assert not evaluate_ns004(DETECTORS["NS004"], {"entity_month_features": months.head(3)}, window())[0]


def test_ns005_only_uses_critical_alerts_without_cases() -> None:
    alerts = pl.DataFrame({"id": ["A1", "A2", "A3", "A4"], "entity_id": ["E1"] * 4, "severity": ["Critical", "Critical", "Critical", "Low"], "has_case": [False, False, True, False], "timestamp": [datetime(2025, 1, i) for i in range(1, 5)]})
    findings, evidence = evaluate_ns005(DETECTORS["NS005"], {"alert_features": alerts}, window())
    assert len(findings) == 1 and findings[0].finding_type == "Missing Investigation" and evidence
    low_only = alerts.with_columns(pl.lit("Low").alias("severity"))
    assert not evaluate_ns005(DETECTORS["NS005"], {"alert_features": low_only}, window())[0]


def test_missing_observation_window_suppresses_time_dependent_findings() -> None:
    empty = pl.DataFrame({"timestamp": pl.Series([], dtype=pl.Datetime)})
    assert not evaluate_ns001(DETECTORS["NS001"], {"asset_features": pl.DataFrame(), "entity_features": pl.DataFrame()}, observation_window({"alert_features": empty}))[0]
