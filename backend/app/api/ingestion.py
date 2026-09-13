from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.ingestion.models import DATASET_NAMES, QualityReport
from app.ingestion.pipeline import IngestionValidationError, ingest_dataset, validate_dataset

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


def _safe_upload_name(filename: str | None) -> str:
    name = Path(filename or "upload").name
    if not name or name in {".", ".."}:
        raise HTTPException(status_code=400, detail="Uploaded file must have a valid filename")
    return name


async def _save_uploads(files: list[UploadFile], directory: Path) -> Path:
    for upload in files:
        destination = directory / _safe_upload_name(upload.filename)
        destination.write_bytes(await upload.read())
    return next(directory.iterdir()) if len(files) == 1 else directory


@router.post("/validate", response_model=QualityReport)
async def validate_upload(
    files: list[UploadFile] = File(...),
    dataset_type: str | None = Query(default=None, alias="type"),
) -> QualityReport:
    """Validate uploads without writing a canonical dataset."""
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")
    if dataset_type is not None and dataset_type not in DATASET_NAMES:
        raise HTTPException(status_code=400, detail=f"Unsupported dataset type: {dataset_type}")
    with tempfile.TemporaryDirectory() as temporary:
        input_path = await _save_uploads(files, Path(temporary))
        return validate_dataset(input_path, dataset_type)


@router.post("/import")
async def import_upload(
    files: list[UploadFile] = File(...),
    dataset_type: str | None = Query(default=None, alias="type"),
) -> dict[str, object]:
    """Validate and commit uploads to the configured local processed directory."""
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")
    if dataset_type is not None and dataset_type not in DATASET_NAMES:
        raise HTTPException(status_code=400, detail=f"Unsupported dataset type: {dataset_type}")
    with tempfile.TemporaryDirectory() as temporary:
        input_path = await _save_uploads(files, Path(temporary))
        try:
            result = ingest_dataset(input_path, dataset_type=dataset_type)
        except IngestionValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.report.model_dump(mode="json")) from exc
        return {
            "dataset_id": result.dataset_id,
            "row_counts": result.row_counts,
            "validation_status": result.validation_status,
            "output_location": result.output_location,
        }
