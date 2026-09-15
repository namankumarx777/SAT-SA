from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.analytics.rules.definitions import enabled_rules
from app.analytics.rules.engine import DEFAULT_OUTPUT, run_rules
from app.analytics.store import PhaseNotFoundError, PhaseStore

router = APIRouter(prefix="/analytics", tags=["rules"])
findings_router = APIRouter(tags=["findings"])


class RuleRunRequest(BaseModel):
    input_path: str
    output_path: str | None = None
    dataset_id: str | None = None


def _phase_store(output_path: str | None) -> PhaseStore:
    return PhaseStore("phase5", Path(output_path) if output_path else DEFAULT_OUTPUT)


@router.post("/rules/run")
def run_rule_endpoint(request: RuleRunRequest) -> dict[str, Any]:
    try:
        result = run_rules(request.input_path, request.output_path or DEFAULT_OUTPUT, request.dataset_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "rules_evaluated": result.rules_evaluated,
        "finding_count": len(result.findings),
        "evidence_count": len(result.evidence),
        "output_location": request.output_path or str(DEFAULT_OUTPUT),
    }


@router.get("/rules")
def get_rules() -> list[dict[str, Any]]:
    return [rule.model_dump() for rule in enabled_rules()]


@findings_router.get("/findings")
def get_findings(output_path: str | None = None) -> list[dict[str, Any]]:
    return _phase_store(output_path).read_findings()


@findings_router.get("/findings/{finding_id}")
def get_finding(finding_id: str, output_path: str | None = None) -> dict[str, Any]:
    try:
        detail = _phase_store(output_path).get_finding(finding_id)
    except PhaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"finding": detail.finding, "evidence": detail.evidence}
