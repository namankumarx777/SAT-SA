from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.security import safe_resolve_path
from app.config import settings

from app.analytics.execution_gap.definitions import DETECTORS
from app.analytics.execution_gap.engine import DEFAULT_OUTPUT, run_execution_gap
from app.analytics.store import PhaseNotFoundError, PhaseStore

router = APIRouter(prefix="/analytics/execution-gap", tags=["execution-gap"])


class ExecutionGapRequest(BaseModel):
    model_config = {"extra": "forbid"}
    input_path: str = Field(..., description="Path to phase5 output")
    output_path: str | None = Field(default=None, description="Path to output directory")
    dataset_id: str | None = Field(default=None, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")


def _phase_store(output_path: str | None) -> PhaseStore:
    path = safe_resolve_path(settings.data_dir, output_path) if output_path else DEFAULT_OUTPUT
    return PhaseStore("phase6", path)


@router.post("/run")
def run_endpoint(request: ExecutionGapRequest) -> dict[str, Any]:
    try:
        in_path = safe_resolve_path(settings.data_dir, request.input_path)
        out_path = safe_resolve_path(settings.data_dir, request.output_path) if request.output_path else DEFAULT_OUTPUT
        result = run_execution_gap(in_path, out_path, request.dataset_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "detectors_evaluated": result.detectors_evaluated,
        "finding_count": len(result.findings),
        "evidence_count": len(result.evidence),
        "output_location": request.output_path or str(DEFAULT_OUTPUT),
    }


@router.get("/rules")
def get_detectors() -> list[dict[str, Any]]:
    return [detector.model_dump() for detector in DETECTORS.values()]


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
