from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

DatasetName = Literal["entities", "assets", "alerts", "cases", "escalations"]
DATASET_NAMES: tuple[str, ...] = ("entities", "assets", "alerts", "cases", "escalations")

REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "entities": ("id", "name", "sector", "size", "criticality"),
    "assets": ("id", "entity_id", "asset_type", "criticality", "expected_monitoring"),
    "alerts": ("id", "entity_id", "asset_id", "timestamp", "severity", "source", "status"),
    "cases": ("id", "entity_id", "alert_id", "opened_at", "investigation_text", "disposition", "escalated", "remediation_recorded"),
    "escalations": ("id", "entity_id", "case_id", "created_at", "escalation_type"),
}
OPTIONAL_COLUMNS: dict[str, tuple[str, ...]] = {
    "entities": ("created_at",),
    "assets": ("monitoring_source",),
    "alerts": ("acknowledged_at", "closed_at", "case_id"),
    "cases": ("closed_at",),
    "escalations": (),
}

CATEGORY_VALUES = {
    "severity": {"Low", "Medium", "High", "Critical"},
    "status": {"Open", "Acknowledged", "Closed"},
    "disposition": {"True Positive", "False Positive", "Benign", "Duplicate"},
}


class QualityIssue(BaseModel):
    dataset: str
    row: int | None = None
    field: str | None = None
    error_type: str
    message: str
    severity: Literal["error", "warning"] = "error"


class QualityReport(BaseModel):
    status: Literal["passed", "failed"]
    files: int = 0
    rows: dict[str, int] = Field(default_factory=dict)
    errors: int = 0
    warnings: int = 0
    issues: list[QualityIssue] = Field(default_factory=list)
    summary: str = ""


class SourceFile(BaseModel):
    filename: str
    size: int
    sha256: str


class Manifest(BaseModel):
    dataset_id: str
    ingested_at: datetime
    source_files: list[SourceFile]
    row_counts: dict[str, int]
    schema_version: str = "1.0"
    validation_status: Literal["passed"] = "passed"
    output_location: str


class IngestionResult(BaseModel):
    dataset_id: str
    row_counts: dict[str, int]
    validation_status: Literal["passed"]
    output_location: str
    manifest: Manifest


class InputSource(BaseModel):
    path: Path
    dataset: str


class ValidationContext(BaseModel):
    input_path: str
    dataset_type: str | None = None
