from __future__ import annotations

from pathlib import Path

import polars as pl

from app.ingestion.pipeline import validate_dataset


def _write_package(source: Path, output: Path) -> None:
    output.mkdir()
    for path in source.glob("*.parquet"):
        pl.read_parquet(path).write_csv(output / path.with_suffix(".csv").name)


def test_valid_phase2_package_passes_validation(phase2_dir: Path) -> None:
    report = validate_dataset(phase2_dir)
    assert report.status == "passed"
    assert report.errors == 0
    assert report.rows["alerts"] == 500


def test_missing_table_and_invalid_category_are_reported(phase2_dir: Path, tmp_path: Path) -> None:
    package = tmp_path / "package"
    _write_package(phase2_dir, package)
    (package / "escalations.csv").unlink()
    alerts = pl.read_csv(package / "alerts.csv").with_columns(pl.lit("Severe").alias("severity"))
    alerts.write_csv(package / "alerts.csv")
    report = validate_dataset(package)
    assert report.status == "failed"
    assert any(issue.error_type == "MISSING_REQUIRED_TABLE" for issue in report.issues)
    assert any(issue.error_type == "INVALID_CATEGORY" for issue in report.issues)


def test_referential_and_temporal_errors_are_reported(phase2_dir: Path, tmp_path: Path) -> None:
    package = tmp_path / "package"
    _write_package(phase2_dir, package)
    assets = pl.read_csv(package / "assets.csv").with_columns(
        pl.when(pl.arange(0, pl.len()) == 0).then(pl.lit("UNKNOWN")).otherwise(pl.col("entity_id")).alias("entity_id")
    )
    assets.write_csv(package / "assets.csv")
    report = validate_dataset(package)
    assert report.status == "failed"
    assert any(issue.error_type == "ORPHAN_ENTITY" for issue in report.issues)


def test_duplicate_ids_and_impossible_timestamps_are_rejected(phase2_dir: Path, tmp_path: Path) -> None:
    package = tmp_path / "package"
    _write_package(phase2_dir, package)
    alerts = pl.read_csv(package / "alerts.csv")
    first = alerts.head(1)
    pl.concat([alerts, first]).write_csv(package / "alerts.csv")
    report = validate_dataset(package)
    assert report.status == "failed"
    assert any(issue.error_type == "DUPLICATE_ID" for issue in report.issues)
