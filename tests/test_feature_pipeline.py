from __future__ import annotations

import hashlib
import json
from pathlib import Path

import duckdb
import polars as pl

from app.analytics.features.feature_pipeline import generate_features


def test_feature_pipeline_outputs_preserve_source_rows_and_are_queryable(phase2_dir: Path, tmp_path: Path) -> None:
    output = tmp_path / "features"
    tables = generate_features(phase2_dir, output, "fixture")
    assert tables["alert_features"].height == pl.read_parquet(phase2_dir / "alerts.parquet").height
    assert tables["case_features"].height == pl.read_parquet(phase2_dir / "cases.parquet").height
    assert tables["asset_features"].height == pl.read_parquet(phase2_dir / "assets.parquet").height
    assert tables["entity_features"].height == pl.read_parquet(phase2_dir / "entities.parquet").height
    assert tables["entity_month_features"].height > 0
    assert not any(column in tables["entity_features"].columns for column in ["risk_score", "negative_space", "is_execution_gap"])
    manifest = json.loads((output / "feature_manifest.json").read_text(encoding="utf-8"))
    assert manifest["dataset_id"] == "fixture"
    for path in output.glob("*.parquet"):
        assert duckdb.sql(f"select count(*) from read_parquet('{path.as_posix()}')").fetchone()[0] > 0


def test_feature_pipeline_is_deterministic_except_generation_metadata(phase2_dir: Path, tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_tables = generate_features(phase2_dir, first, "fixture")
    second_tables = generate_features(phase2_dir, second, "fixture")
    for name in first_tables:
        assert first_tables[name].equals(second_tables[name])
        assert hashlib.sha256((first / f"{name}.parquet").read_bytes()).digest() == hashlib.sha256((second / f"{name}.parquet").read_bytes()).digest()
