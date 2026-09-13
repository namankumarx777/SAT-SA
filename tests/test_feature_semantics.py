from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from app.analytics.features.feature_pipeline import generate_features
from app.analytics.features.schemas import RAPID_CLOSURE_MINUTES

FORBIDDEN_LABELS = {
    "risk_score", "negative_space", "execution_gap", "is_execution_gap",
    "is_negative_space", "review_priority", "peer_deviation", "investigation_weakness",
}


def _full_features(tmp_path: Path) -> dict[str, pl.DataFrame]:
    source = Path(__file__).resolve().parents[1] / "data" / "synthetic"
    return generate_features(source, tmp_path / "features", "semantic-fixture")


def test_repeat_rates_have_distinct_event_and_asset_semantics(tmp_path: Path) -> None:
    tables = _full_features(tmp_path)
    entity = tables["entity_features"]
    assert {"repeat_alert_event_rate", "repeat_alert_asset_rate"} <= set(entity.columns)
    assert "repeat_asset_alert_rate" not in entity.columns
    assert ((entity["repeat_alert_event_rate"] >= 0) & (entity["repeat_alert_event_rate"] <= 1)).all()
    assert ((entity["repeat_alert_asset_rate"] >= 0) & (entity["repeat_alert_asset_rate"] <= 1)).all()
    assert tables["alert_features"]["asset_alert_count"].min() >= 1


def test_negative_space_features_preserve_coverage_gap(tmp_path: Path) -> None:
    entity = _full_features(tmp_path)["entity_features"]
    target = entity.filter(pl.col("entity_id").is_in(["CSE-007", "CSE-008"]))
    baseline = entity.filter(~pl.col("entity_id").is_in(["CSE-007", "CSE-008"]))
    assert target["expected_monitored_assets_without_activity"].sum() > 0
    assert target["monitoring_coverage_rate"].mean() < baseline["monitoring_coverage_rate"].mean()
    assert target["critical_asset_activity_rate"].mean() < baseline["critical_asset_activity_rate"].mean()
    assert not FORBIDDEN_LABELS & set(entity.columns)


def test_execution_gap_features_preserve_critical_behavior(tmp_path: Path) -> None:
    entity = _full_features(tmp_path)["entity_features"]
    target = entity.filter(pl.col("entity_id").is_in(["CSE-004", "CSE-011"]))
    baseline = entity.filter(~pl.col("entity_id").is_in(["CSE-004", "CSE-011"]))
    assert target["critical_case_count"].sum() > 0
    assert target["critical_escalation_rate"].mean() < baseline["critical_escalation_rate"].mean()
    assert target["critical_median_investigation_minutes"].mean() < baseline["critical_median_investigation_minutes"].mean()
    assert not FORBIDDEN_LABELS & set(entity.columns)


def test_zero_denominators_are_null_and_rapid_rate_uses_closed_cases(tmp_path: Path) -> None:
    tables = _full_features(tmp_path)
    entity = tables["entity_features"]
    no_critical = entity.filter(pl.col("critical_case_count") == 0)
    assert no_critical["critical_escalation_rate"].null_count() == no_critical.height
    no_expected = entity.filter(pl.col("expected_monitored_assets") == 0)
    assert no_expected["monitoring_coverage_rate"].null_count() == no_expected.height
    cases = tables["case_features"]
    assert cases.filter(pl.col("closed_at").is_null())["investigation_minutes"].null_count() == cases.filter(pl.col("closed_at").is_null()).height
    assert cases.filter(pl.col("closed_at").is_null())["case_age_at_close_minutes"].null_count() == cases.filter(pl.col("closed_at").is_null()).height
    manifest = json.loads((tmp_path / "features" / "feature_manifest.json").read_text(encoding="utf-8"))
    definitions = {item["name"]: item for item in manifest["features"]}
    assert "closed_case_count" in definitions["rapid_closure_rate"]["formula"]
    assert RAPID_CLOSURE_MINUTES == 10


def test_feature_metadata_and_monthly_absence_semantics(tmp_path: Path) -> None:
    tables = _full_features(tmp_path)
    manifest = json.loads((tmp_path / "features" / "feature_manifest.json").read_text(encoding="utf-8"))
    definitions = manifest["features"]
    assert all({"name", "type", "description", "source", "formula", "nullable", "units"} <= set(item) for item in definitions)
    assert "only entity-months with observed" in manifest["monthly_semantics"]
    assert not FORBIDDEN_LABELS & set().union(*(set(frame.columns) for frame in tables.values()))
