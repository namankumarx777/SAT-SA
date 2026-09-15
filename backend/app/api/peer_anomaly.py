from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.analytics.peer_anomaly.definitions import DETECTORS
from app.analytics.peer_anomaly.engine import DEFAULT_OUTPUT, run_peer_anomaly
from app.analytics.store import PhaseNotFoundError, PhaseStore

router = APIRouter(prefix="/analytics/peer-anomaly", tags=["peer-anomaly"])


class PeerAnomalyRequest(BaseModel):
    input_path: str
    output_path: str | None = None
    dataset_id: str | None = None


def _phase_store(output_path: str | None) -> PhaseStore:
    return PhaseStore("phase8", Path(output_path) if output_path else DEFAULT_OUTPUT)


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
    return _phase_store(output_path).read_findings()


@router.get("/findings/{finding_id}")
def get_finding(finding_id: str, output_path: str | None = None) -> dict[str, Any]:
    try:
        detail = _phase_store(output_path).get_finding(finding_id)
    except PhaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"finding": detail.finding, "evidence": detail.evidence}
