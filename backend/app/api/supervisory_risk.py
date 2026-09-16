from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.security import safe_resolve_path
from app.config import settings

from app.analytics.supervisory_risk.engine import DEFAULT_OUTPUT, run_supervisory_risk

router = APIRouter(prefix="/analytics/supervisory-risk", tags=["supervisory-risk"])

REPO_ROOT = Path(__file__).resolve().parents[3]


class SupervisoryRiskRequest(BaseModel):
    model_config = {"extra": "forbid"}
    input_path: str = Field(..., description="Path to input directory")
    output_path: str | None = Field(default=None, description="Path to output directory")
    dataset_id: str | None = Field(default=None, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")


def _get_output_path(output_path: str | None) -> Path:
    if output_path:
        return safe_resolve_path(settings.data_dir, output_path)
    candidates = [
        REPO_ROOT / "data" / "processed" / "supervisory_risk-final",
        Path("data/processed/supervisory_risk-final"),
        Path("../data/processed/supervisory_risk-final"),
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return DEFAULT_OUTPUT


@router.post("/run")
def run_endpoint(request: SupervisoryRiskRequest) -> dict[str, Any]:
    try:
        in_path = safe_resolve_path(settings.data_dir, request.input_path)
        out_path = safe_resolve_path(settings.data_dir, request.output_path) if request.output_path else DEFAULT_OUTPUT
        result = run_supervisory_risk(in_path, out_path, request.dataset_id)
        dest = str(out_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "entities_evaluated": len(result.entities_evaluated),
        "risk_contributions_count": len(result.risk_contributions),
        "review_queue_count": len(result.review_queue),
        "output_location": dest,
    }


def _enrich_entity_risks(risk_df: pl.DataFrame) -> list[dict[str, Any]]:
    candidates = [
        REPO_ROOT / "data" / "processed" / "phase4-features" / "entity_features.parquet",
        REPO_ROOT / "data" / "processed" / "entity_features.parquet",
        Path("data/processed/phase4-features/entity_features.parquet"),
        Path("../data/processed/phase4-features/entity_features.parquet"),
    ]
    meta_path = next((p for p in candidates if p.is_file()), None)
    if meta_path:
        meta_cols = ["entity_id", "name", "sector", "size", "criticality"]
        meta_df = pl.read_parquet(meta_path)
        avail_cols = [c for c in meta_cols if c in meta_df.columns]
        if "entity_id" in avail_cols and len(avail_cols) > 1:
            meta_df = meta_df.select(avail_cols)
            return risk_df.join(meta_df, on="entity_id", how="left").to_dicts()
    return risk_df.to_dicts()


@router.get("/entities")
def get_entities(output_path: str | None = None) -> list[dict[str, Any]]:
    path = _get_output_path(output_path) / "entity_risk.parquet"
    if not path.is_file():
        return []
    df = pl.read_parquet(path)
    return _enrich_entity_risks(df)


@router.get("/entities/{entity_id}")
def get_entity(entity_id: str, output_path: str | None = None) -> dict[str, Any]:
    path = _get_output_path(output_path) / "entity_risk.parquet"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Entity risk dataset not found")
    df = pl.read_parquet(path).filter(pl.col("entity_id") == entity_id)
    if df.is_empty():
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found in risk assessment")
    enriched = _enrich_entity_risks(df)
    return enriched[0]


def _normalize_dict_lists(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    import json
    for r in records:
        sf = r.get("supporting_finding_ids")
        if isinstance(sf, str):
            try:
                r["supporting_finding_ids"] = json.loads(sf)
            except Exception:
                r["supporting_finding_ids"] = [sf]
    return records


@router.get("/contributions/{entity_id}")
def get_contributions(entity_id: str, output_path: str | None = None) -> list[dict[str, Any]]:
    path = _get_output_path(output_path) / "risk_contributions.parquet"
    if not path.is_file():
        return []
    records = pl.read_parquet(path).filter(pl.col("entity_id") == entity_id).to_dicts()
    return _normalize_dict_lists(records)


@router.get("/manifest")
def get_manifest(output_path: str | None = None) -> dict[str, Any]:
    import json
    from app.analytics.supervisory_risk.config import DIMENSION_METADATA
    path = _get_output_path(output_path) / "supervisory_risk_manifest.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Supervisory risk manifest not found")
    with open(path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    # Backward compatibility: older committed manifests predate dimensions_config.
    # The canonical dimension configuration always lives in config, so merge it here.
    if "dimensions_config" not in manifest:
        manifest["dimensions_config"] = DIMENSION_METADATA
    return manifest


@router.get("/findings/{finding_id}")
def get_finding_detail(finding_id: str, input_path: str | None = None) -> dict[str, Any]:
    from dataclasses import asdict
    from app.analytics.supervisory_risk.inputs import load_upstream_bundle
    if input_path:
        in_dir = safe_resolve_path(settings.data_dir, input_path)
    else:
        candidates = [
            REPO_ROOT / "data" / "processed",
            Path("data/processed"),
            Path("../data/processed"),
        ]
        in_dir = next((p for p in candidates if p.is_dir()), Path("data/processed"))
    try:
        bundle = load_upstream_bundle(in_dir)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed loading upstream data: {exc}") from exc

    target_finding = next((f for f in bundle.findings if f.id == finding_id), None)
    if not target_finding:
        raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found across upstream phases")

    ev_list = bundle.evidence_by_finding.get(finding_id, [])
    return {
        "finding": asdict(target_finding),
        "evidence": [asdict(e) for e in ev_list],
    }


@router.get("/review-queue")
def get_review_queue(output_path: str | None = None) -> list[dict[str, Any]]:
    path = _get_output_path(output_path) / "review_queue.parquet"
    if not path.is_file():
        return []
    records = pl.read_parquet(path).sort("rank").to_dicts()
    return _normalize_dict_lists(records)


@router.get("/review-queue/{record_id}")
def get_review_queue_item(record_id: str, output_path: str | None = None) -> dict[str, Any]:
    path = _get_output_path(output_path) / "review_queue.parquet"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Review queue dataset not found")
    rows = pl.read_parquet(path).filter(pl.col("record_id") == record_id).to_dicts()
    if not rows:
        raise HTTPException(status_code=404, detail=f"Review queue item {record_id} not found")
    return _normalize_dict_lists(rows)[0]


@router.get("/entities/{entity_id}/dossier")
def get_entity_dossier(entity_id: str, input_path: str | None = None) -> dict[str, Any]:
    from app.analytics.supervisory_risk.dossier import generate_entity_dossier_data
    in_dir = safe_resolve_path(settings.data_dir, input_path) if input_path else (REPO_ROOT / "data" / "processed")
    try:
        return generate_entity_dossier_data(entity_id, in_dir)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed generating dossier: {exc}") from exc


@router.get("/entities/{entity_id}/dossier/html")
def get_entity_dossier_html(entity_id: str, input_path: str | None = None) -> Any:
    from fastapi.responses import HTMLResponse
    from app.analytics.supervisory_risk.dossier import generate_entity_dossier_data, render_entity_dossier_html
    in_dir = safe_resolve_path(settings.data_dir, input_path) if input_path else (REPO_ROOT / "data" / "processed")
    try:
        data = generate_entity_dossier_data(entity_id, in_dir)
        html_content = render_entity_dossier_html(data)
        return HTMLResponse(content=html_content, status_code=200)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed rendering dossier HTML: {exc}") from exc



