from __future__ import annotations

import json
from pathlib import Path

import duckdb
import polars as pl
from fastapi.testclient import TestClient

from app.ingestion.pipeline import ingest_dataset
from app.main import app


def test_import_writes_canonical_parquet_and_manifest(phase2_dir: Path, tmp_path: Path) -> None:
    result = ingest_dataset(phase2_dir, tmp_path / "processed")
    output = tmp_path / "processed" / result.dataset_id
    assert result.validation_status == "passed"
    assert result.row_counts["alerts"] == 500
    assert {path.name for path in output.glob("*.parquet")} == {
        "entities.parquet", "assets.parquet", "alerts.parquet", "cases.parquet", "escalations.parquet",
    }
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["validation_status"] == "passed"
    assert len(manifest["source_files"]) == 5
    assert all(len(item["sha256"]) == 64 for item in manifest["source_files"])
    assert duckdb.sql(f"select count(*) from read_parquet('{(output / 'alerts.parquet').as_posix()}')").fetchone()[0] == 500


def test_single_json_table_can_be_validated_and_imported(phase2_dir: Path, tmp_path: Path) -> None:
    source = tmp_path / "alerts.json"
    alerts = pl.read_parquet(phase2_dir / "alerts.parquet")
    alerts.write_json(source)
    result = ingest_dataset(source, tmp_path / "processed", "alerts")
    assert result.row_counts == {"alerts": 500}
    assert (tmp_path / "processed" / result.dataset_id / "alerts.parquet").exists()


def test_api_validate_and_import_endpoints(phase2_dir: Path, monkeypatch, tmp_path: Path) -> None:
    import app.api.ingestion as ingestion_api

    monkeypatch.setattr(
        ingestion_api,
        "ingest_dataset",
        lambda input_path, dataset_type=None: ingest_dataset(input_path, tmp_path / "processed", dataset_type),
    )
    files = [
        ("files", (path.name, path.read_bytes(), "application/octet-stream"))
        for path in sorted(phase2_dir.glob("*.parquet"))
    ]
    client = TestClient(app)
    validation = client.post("/ingestion/validate", files=files)
    assert validation.status_code == 200
    assert validation.json()["status"] == "passed"
    imported = client.post("/ingestion/import", files=files)
    assert imported.status_code == 200
    assert imported.json()["validation_status"] == "passed"
