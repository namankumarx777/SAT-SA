from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.analytics.peer_anomaly.definitions import DETECTORS
from app.analytics.peer_anomaly.engine import DEFAULT_OUTPUT, run_peer_anomaly

router = APIRouter(prefix="/analytics/peer-anomaly", tags=["peer-anomaly"])


class PeerAnomalyRequest(BaseModel):
    input_path: str
    output_path: str | None = None
    dataset_id: str | None = None


@router.post("/run")
def run_endpoint(request: PeerAnomalyRequest) -> dict[str, Any]:
    try:
        result = run_peer_anomaly(request.input_path, request.output_path or DEFAULT_OUTPUT, request.dataset_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"finding_count": len(result.findings), "evidence_count": len(result.evidence), "cohort_count": result.cohort_count, "anomalies": result.anomalies, "output_location": request.output_path or str(DEFAULT_OUTPUT)}


@router.get("/rules")
def get_rules() -> list[dict[str, Any]]:
    return [definition.model_dump() for definition in DETECTORS.values()]


@router.get("/findings")
def get_findings(output_path: str | None = None) -> list[dict[str, Any]]:
    path = Path(output_path) if output_path else DEFAULT_OUTPUT
    return [] if not (path / "findings.parquet").is_file() else pl.read_parquet(path / "findings.parquet").to_dicts()


@router.get("/findings/{finding_id}")
def get_finding(finding_id: str, output_path: str | None = None) -> dict[str, Any]:
    path = Path(output_path) if output_path else DEFAULT_OUTPUT
    finding_path = path / "findings.parquet"
    if not finding_path.is_file():
        raise HTTPException(status_code=404, detail="Finding not found")
    rows = pl.read_parquet(finding_path).filter(pl.col("id") == finding_id).to_dicts()
    if not rows:
        raise HTTPException(status_code=404, detail="Finding not found")
    evidence_path = path / "evidence.parquet"
    evidence = [] if not evidence_path.is_file() else pl.read_parquet(evidence_path).filter(pl.col("finding_id") == finding_id).to_dicts()
    return {"finding": rows[0], "evidence": evidence}
