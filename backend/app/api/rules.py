from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.analytics.rules.definitions import enabled_rules
from app.analytics.rules.engine import DEFAULT_OUTPUT, run_rules

router = APIRouter(prefix="/analytics", tags=["rules"])
findings_router = APIRouter(tags=["findings"])


class RuleRunRequest(BaseModel):
    input_path: str
    output_path: str | None = None
    dataset_id: str | None = None


def _read_findings(output: Path) -> list[dict[str, Any]]:
    path = output / "findings.parquet"
    if not path.is_file():
        return []
    return pl.read_parquet(path).to_dicts()


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
    return _read_findings(Path(output_path) if output_path else DEFAULT_OUTPUT)


@findings_router.get("/findings/{finding_id}")
def get_finding(finding_id: str, output_path: str | None = None) -> dict[str, Any]:
    output = Path(output_path) if output_path else DEFAULT_OUTPUT
    findings = [row for row in _read_findings(output) if row["id"] == finding_id]
    if not findings:
        raise HTTPException(status_code=404, detail="Finding not found")
    evidence_path = output / "evidence.parquet"
    evidence = [] if not evidence_path.is_file() else pl.read_parquet(evidence_path).filter(pl.col("finding_id") == finding_id).to_dicts()
    return {"finding": findings[0], "evidence": evidence}
