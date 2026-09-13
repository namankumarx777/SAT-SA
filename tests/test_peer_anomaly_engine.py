from __future__ import annotations

import hashlib
import json
from pathlib import Path

import duckdb
import polars as pl
from fastapi.testclient import TestClient

from app.analytics.features.feature_pipeline import generate_features
from app.analytics.peer_anomaly.engine import run_peer_anomaly
from app.main import app


def test_peer_anomaly_engine_outputs_are_traceable_and_deterministic(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[1] / "data" / "synthetic"
    features = tmp_path / "features"
    generate_features(source, features, "phase2-canonical")
    first, second = tmp_path / "first", tmp_path / "second"
    result = run_peer_anomaly(features, first, "phase2-canonical")
    run_peer_anomaly(features, second, "phase2-canonical")
    assert result.findings and result.evidence
    assert result.cohort_count >= 1 and result.anomalies >= 0
    finding_ids = {item.id for item in result.findings}
    assert all(item.finding_id in finding_ids for item in result.evidence)
    for name in ["findings", "evidence"]:
        left, right = first / f"{name}.parquet", second / f"{name}.parquet"
        assert hashlib.sha256(left.read_bytes()).digest() == hashlib.sha256(right.read_bytes()).digest()
        assert duckdb.sql(f"select count(*) from read_parquet('{left.as_posix()}')").fetchone()[0] > 0
    manifest = json.loads((first / "peer_anomaly_manifest.json").read_text(encoding="utf-8"))
    assert manifest["cohort_definition"] == ["sector", "size", "criticality"]
    assert "not statistical confidence" in manifest["evidence_strength_methodology"]
    assert not {"risk_score", "is_peer_deviation", "ground_truth"} & set(pl.read_parquet(first / "findings.parquet").columns)


def test_peer_anomaly_api_endpoints(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[1] / "data" / "processed" / "phase4-final"
    output = tmp_path / "api-output"
    client = TestClient(app)
    rules = client.get("/analytics/peer-anomaly/rules")
    assert rules.status_code == 200
    run = client.post("/analytics/peer-anomaly/run", json={"input_path": str(source), "output_path": str(output), "dataset_id": "api-test"})
    assert run.status_code == 200
    findings = client.get("/analytics/peer-anomaly/findings", params={"output_path": str(output)})
    assert findings.status_code == 200 and findings.json()
    detail = client.get(f"/analytics/peer-anomaly/findings/{findings.json()[0]['id']}", params={"output_path": str(output)})
    assert detail.status_code == 200 and detail.json()["evidence"]
